import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly_calplot import calplot

from config import settings
from dashboard_theme import DASHBOARD_COLORS
from trello_client import update_card_due_date

st.set_page_config(page_title="Task Analytics Dashboard", page_icon="📊", layout="wide")


@st.cache_data
def load_data():
    all_tasks = pd.read_csv(settings.ALL_DATA_PATH)
    done_tasks = pd.read_csv(settings.DONE_DATA_PATH)
    pending_tasks = pd.read_csv(settings.PENDING_DATA_PATH)

    all_tasks["card_due"] = pd.to_datetime(all_tasks.get("card_due"), errors="coerce", utc=True)
    done_tasks["done_date"] = pd.to_datetime(done_tasks.get("done_date"), errors="coerce", utc=True)
    pending_tasks["card_due"] = pd.to_datetime(pending_tasks.get("card_due"), errors="coerce", utc=True)

    return all_tasks, done_tasks, pending_tasks


def compute_metrics(tasks_df: pd.DataFrame) -> tuple[int, int, int, float]:
    total = len(tasks_df)
    completed = len(tasks_df[tasks_df["status"] == "Done"])
    pending = total - completed
    completion_rate = (completed / total * 100) if total else 0.0
    return total, completed, pending, completion_rate


def filter_data(
    all_tasks: pd.DataFrame,
    done_tasks: pd.DataFrame,
    pending_tasks: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, tuple[pd.Timestamp, pd.Timestamp]]:
    st.sidebar.header("Filters")

    status_options = sorted(all_tasks["status"].dropna().unique().tolist())
    selected_status = st.sidebar.multiselect("Status", status_options, default=status_options)

    list_pool = sorted(
        set(all_tasks.get("list", pd.Series(dtype=str)).dropna().tolist())
        | set(done_tasks.get("origin_list", pd.Series(dtype=str)).dropna().tolist())
        | set(pending_tasks.get("list", pd.Series(dtype=str)).dropna().tolist())
    )
    selected_lists = st.sidebar.multiselect("Lists", list_pool, default=list_pool)

    task_query = st.sidebar.text_input("Task contains", "").strip().lower()

    today_utc = pd.Timestamp.now(tz="UTC").normalize()
    done_dates = done_tasks["done_date"].dropna()
    min_done = done_dates.min().date() if not done_dates.empty else today_utc.date()
    max_done = done_dates.max().date() if not done_dates.empty else today_utc.date()

    done_range = st.sidebar.date_input(
        "Done date range",
        value=(min_done, max_done),
        min_value=min_done,
        max_value=max_done,
    )
    if len(done_range) != 2:
        done_start, done_end = min_done, max_done
    else:
        done_start, done_end = done_range

    due_dates = pending_tasks["card_due"].dropna()
    min_due = due_dates.min().date() if not due_dates.empty else today_utc.date()
    max_due = due_dates.max().date() if not due_dates.empty else today_utc.date()

    due_range = st.sidebar.date_input(
        "Pending due date range",
        value=(min_due, max_due),
        min_value=min_due,
        max_value=max_due,
    )
    if len(due_range) != 2:
        due_start, due_end = min_due, max_due
    else:
        due_start, due_end = due_range

    filtered_all = all_tasks.copy()
    if selected_status:
        filtered_all = filtered_all[filtered_all["status"].isin(selected_status)]
    if selected_lists:
        filtered_all = filtered_all[filtered_all["list"].isin(selected_lists)]
    if task_query:
        filtered_all = filtered_all[filtered_all["card"].fillna("").str.lower().str.contains(task_query)]

    filtered_done = done_tasks.copy()
    if selected_lists:
        filtered_done = filtered_done[filtered_done["origin_list"].isin(selected_lists)]
    if task_query:
        filtered_done = filtered_done[filtered_done["card"].fillna("").str.lower().str.contains(task_query)]
    done_start_ts = pd.Timestamp(done_start, tz="UTC")
    done_end_ts = pd.Timestamp(done_end, tz="UTC") + pd.Timedelta(days=1)
    filtered_done = filtered_done[
        (filtered_done["done_date"] >= done_start_ts) & (filtered_done["done_date"] < done_end_ts)
    ]

    filtered_pending = pending_tasks.copy()
    if selected_lists:
        filtered_pending = filtered_pending[filtered_pending["list"].isin(selected_lists)]
    if task_query:
        filtered_pending = filtered_pending[filtered_pending["card"].fillna("").str.lower().str.contains(task_query)]
    due_start_ts = pd.Timestamp(due_start, tz="UTC")
    due_end_ts = pd.Timestamp(due_end, tz="UTC") + pd.Timedelta(days=1)
    filtered_pending = filtered_pending[
        (filtered_pending["card_due"] >= due_start_ts) & (filtered_pending["card_due"] < due_end_ts)
    ]

    return filtered_all, filtered_done, filtered_pending, (done_start_ts, done_end_ts - pd.Timedelta(days=1))


def render_due_date_updater(tasks_df: pd.DataFrame) -> None:
    with st.expander("🔧 Update Trello Due Date (Remote)", expanded=False):
        pending_cards_df = (
            tasks_df[tasks_df["status"] == "Not Done"][["card", "card_id", "list", "card_due"]]
            .dropna(subset=["card_id"])
            .sort_values(by=["list", "card"])
        )

        if pending_cards_df.empty:
            st.info("No pending tasks with card IDs were found.")
            return

        task_label_map = {
            f"{row.card} ({row.list})": row.card_id for row in pending_cards_df.itertuples(index=False)
        }
        selected_label = st.selectbox("Choose pending task", options=list(task_label_map.keys()))
        selected_due = st.date_input("New due date", value=pd.Timestamp.today().date())

        if st.button("Update due date in Trello", type="primary"):
            selected_card_id = task_label_map[selected_label]
            try:
                update_card_due_date(selected_card_id, selected_due)
                st.success(
                    "Due date updated in Trello. Run data refresh "
                    "(`python fetch_trello_data.py` then `python data_processing.py`) "
                    "to sync local CSV files."
                )
            except Exception as exc:
                st.error(f"Could not update due date: {exc}")


def remove_timezones(value: str) -> str:
    return value.split()[0]


all_df, done_df, pending_df = load_data()
filtered_df, filtered_done_df, filtered_pending_df, (period_start, period_end) = filter_data(
    all_df, done_df, pending_df
)

total_tasks, completed_tasks, pending_tasks, _ = compute_metrics(filtered_df)

st.title("📊 Task Analytics Dashboard")
st.caption(f"**Filtered Period:** {period_start.date()} to {period_end.date()}")
render_due_date_updater(filtered_df)

col1, col2, col3 = st.columns(3)

with col1:
    done_with_weekday = filtered_done_df.copy()
    done_with_weekday["weekday"] = done_with_weekday["done_date"].dt.day_name()
    most_productive = done_with_weekday["weekday"].value_counts().idxmax() if not done_with_weekday.empty else "N/A"
    st.metric("Best Day", most_productive, border=True)

with col2:
    left, center, right = st.columns(3)
    with left:
        st.metric("Total", total_tasks, border=True)
    with center:
        st.metric("Completed", completed_tasks, border=True)
    with right:
        st.metric("Pending", pending_tasks, border=True)

with col3:
    days_in_period = max((period_end.date() - period_start.date()).days + 1, 1)
    avg_daily = len(filtered_done_df) / days_in_period
    st.metric("Avg Tasks/Day", f"{avg_daily:.2f}", border=True)

st.divider()
left, right = st.columns([2, 2])

with left:
    task_counts = (
        filtered_df[filtered_df["status"] == "Not Done"].groupby("list").size().reset_index(name="count")
    )
    fig = px.bar(task_counts, x="list", y="count", title="Not Done Tasks per List", height=350)
    fig.update_layout(title_x=0.4, margin=dict(l=20, r=20, t=50, b=40))
    st.plotly_chart(fig, use_container_width=True)

with right:
    daily_tasks = filtered_done_df.groupby(filtered_done_df["done_date"].dt.date).size()
    all_days = pd.date_range(start=period_start.date(), end=period_end.date(), freq="D").date
    daily_tasks = daily_tasks.reindex(all_days, fill_value=0)
    daily_df_chart = pd.DataFrame({"Date": daily_tasks.index, "Tasks Completed": daily_tasks.values})
    fig = px.line(daily_df_chart, x="Date", y="Tasks Completed", title="Daily Progress")
    fig.update_layout(title_x=0.45, margin=dict(l=20, r=20, t=50, b=40), height=400)
    st.plotly_chart(fig, use_container_width=True)

st.divider()
left, right = st.columns([2, 2])

with right:
    fig = px.pie(
        task_counts,
        names="list",
        values="count",
        title="Not Done Percentage",
        hole=0.3,
        color_discrete_sequence=DASHBOARD_COLORS["categorical"],
    )
    fig.update_layout(title_x=0.3)
    fig.update_traces(textposition="inside", textinfo="percent")
    st.plotly_chart(fig, use_container_width=True)

with left:
    done_task_counts = filtered_done_df["origin_list"].value_counts().reset_index()
    done_task_counts.columns = ["origin_list", "count"]
    done_task_counts = done_task_counts[done_task_counts["origin_list"] != "other"]
    fig = px.pie(
        done_task_counts,
        names="origin_list",
        values="count",
        title="Done Tasks by List",
        hole=0.3,
        color_discrete_sequence=DASHBOARD_COLORS["categorical"],
    )
    fig.update_layout(title_x=0.3)
    fig.update_traces(textposition="inside", textinfo="percent")
    st.plotly_chart(fig, use_container_width=True)

st.divider()
left, right = st.columns([2, 2])

with left:
    day_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    weekly_df = filtered_done_df.copy()
    weekly_df["weekday"] = pd.Categorical(
        weekly_df["done_date"].dt.day_name(), categories=day_order, ordered=True
    )
    weekly_df = weekly_df["weekday"].value_counts().sort_index().reset_index()
    weekly_df.columns = ["Day", "Tasks Completed"]

    fig = px.bar(
        weekly_df,
        x="Day",
        y="Tasks Completed",
        color="Tasks Completed",
        color_continuous_scale=DASHBOARD_COLORS["continuous_scale"],
        text="Tasks Completed",
        title="Tasks-Day Distribution",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

with right:
    daily_tasks = filtered_done_df.groupby(filtered_done_df["done_date"].dt.date).size()
    all_days = pd.date_range(start=period_start.date(), end=period_end.date(), freq="D").date
    daily_tasks = daily_tasks.reindex(all_days, fill_value=0)
    cumulative_df = pd.DataFrame({"Date": daily_tasks.index, "Cumulative Tasks": daily_tasks.values.cumsum()})

    fig = px.area(cumulative_df, x="Date", y="Cumulative Tasks", line_shape="linear")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

incomplete_tasks = filtered_df[filtered_df["status"] == "Not Done"].copy()
old_task_age = settings.OLD_TASK_AGE
incomplete_tasks["age_category"] = incomplete_tasks["card_age"].apply(
    lambda x: f"Old (>{old_task_age} days)" if x > old_task_age else f"New (≤{old_task_age} days)"
)

st.subheader("Tasks Done Today")
now_utc = pd.Timestamp.now(tz="UTC")
start_today = now_utc.normalize()
end_today = start_today + pd.Timedelta(days=1)
done_today = filtered_done_df[
    (filtered_done_df["done_date"] >= start_today) & (filtered_done_df["done_date"] < end_today)
]
if not done_today.empty:
    st.success(f"You completed {len(done_today)} task(s) today")
    st.dataframe(
        done_today[["card", "origin_list"]].rename(columns={"card": "Task Name", "origin_list": "From List"}),
        use_container_width=True,
    )
else:
    st.info("No tasks completed yet today")

st.subheader("Oldest Pending Task")
oldest_tasks = incomplete_tasks.sort_values(by="card_age", ascending=False)[["card", "card_age", "list"]].head(5)
st.dataframe(oldest_tasks, use_container_width=True)

stack_day_order = ["Friday", "Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
stacked_weekly_df = filtered_done_df.copy()
stacked_weekly_df["weekday"] = pd.Categorical(
    stacked_weekly_df["done_date"].dt.day_name(), categories=stack_day_order, ordered=True
)
stacked_weekly_df = (
    stacked_weekly_df[stacked_weekly_df["origin_list"] != "other"]
    .groupby(["weekday", "origin_list"])
    .size()
    .reset_index(name="Tasks Completed")
    .sort_values("weekday")
)

fig = px.bar(
    stacked_weekly_df,
    x="weekday",
    y="Tasks Completed",
    color="origin_list",
    title="Tasks Completed per Day (Grouped by List)",
    text="Tasks Completed",
)
fig.update_layout(barmode="group", height=600)
fig.update_traces(textposition="inside")
st.plotly_chart(fig, use_container_width=True)

# done tasks heatmap
st.divider()
done_df_calplot = filtered_done_df.dropna(subset=["done_date"]).copy()
done_df_calplot["done_date"] = done_df_calplot["done_date"].astype(str).apply(remove_timezones)
done_counts_df = done_df_calplot["done_date"].value_counts().reset_index()
done_counts_df.columns = ["done_date", "count"]
if done_counts_df.empty:
    st.info("No completed-task data is available for the selected filters.")
else:
    fig = calplot(
        done_counts_df,
        x="done_date",
        y="count",
        name="Done Tasks",
        dark_theme=True,
        title="Done Tasks Heatmap",
        month_lines=False,
    )
    fig.update_layout(
        title={"text": "Done Tasks Heatmap", "y": 0.99, "x": 0.5, "xanchor": "center", "yanchor": "top"}
    )
    st.plotly_chart(fig, use_container_width=True)

# pending due dates heatmap
pending_df_calplot = filtered_pending_df.dropna(subset=["card_due"]).copy()
pending_df_calplot["card_due"] = pending_df_calplot["card_due"].astype(str).apply(remove_timezones)
counts_df = pending_df_calplot["card_due"].value_counts().reset_index()
counts_df.columns = ["card_due", "count"]
if counts_df.empty:
    st.info("No pending due-date data is available for the selected filters.")
else:
    fig = calplot(
        counts_df,
        x="card_due",
        y="count",
        dark_theme=True,
        title="Pending Tasks Due Dates",
        colorscale=DASHBOARD_COLORS["heatmap_scale"],
        month_lines=False,
    )
    fig.update_layout(
        title={"text": "Pending Tasks Due Dates", "y": 0.99, "x": 0.5, "xanchor": "center", "yanchor": "top"}
    )
    st.plotly_chart(fig, use_container_width=False)

st.subheader("Overdue Tasks")
today = pd.Timestamp.now(tz="UTC").normalize()
overdue_tasks = filtered_pending_df[filtered_pending_df["card_due"] < today]
st.dataframe(
    overdue_tasks[["card", "list", "card_due"]].rename(
        columns={"card": "Task Name", "list": "List", "card_due": "Due Date"}
    ),
    use_container_width=True,
)

st.subheader("Tasks Due Today")
today_start = pd.Timestamp.now(tz="UTC").normalize()
today_end = today_start + pd.Timedelta(days=1)
pending_due_today = filtered_pending_df[
    (filtered_pending_df["card_due"] >= today_start) & (filtered_pending_df["card_due"] < today_end)
]
if not pending_due_today.empty:
    st.dataframe(
        pending_due_today[["card", "list", "card_due"]].rename(
            columns={"card": "Task Name", "list": "List", "card_due": "Due Date"}
        ),
        use_container_width=True,
    )
else:
    st.info("No tasks are due today.")

due_df = filtered_pending_df.copy()
due_source_col = "list" if "list" in due_df.columns else None

due_df["card_due"] = due_df["card_due"].dt.tz_convert(None).dt.normalize()
due_df = due_df.dropna(subset=["card_due"])

start = pd.Timestamp.today().normalize()
end = start + pd.DateOffset(months=2)
full_range_df = pd.DataFrame({"card_due": pd.date_range(start=start, end=end, freq="D")})

if due_source_col:
    due_df[due_source_col] = due_df[due_source_col].fillna("Unknown")
    counts = due_df.groupby(["card_due", due_source_col]).size().reset_index(name="count")
    counts = full_range_df.merge(counts, on="card_due", how="left")
    counts[due_source_col] = counts[due_source_col].fillna("No Due Cards")
    counts["count"] = counts["count"].fillna(0).astype(int)

    color_palette = DASHBOARD_COLORS["qualitative_fallback"]
    source_values = counts[due_source_col].dropna().unique()
    color_map = {source: color_palette[idx % len(color_palette)] for idx, source in enumerate(sorted(source_values))}

    fig = px.bar(
        counts,
        x="count",
        y="card_due",
        color=due_source_col,
        orientation="h",
        barmode="stack",
        color_discrete_map=color_map,
        labels={"count": "Due Cards", "card_due": "Due Date", due_source_col: "List"},
        title="Pending Due Dates by List",
    )
else:
    counts = due_df.groupby("card_due").size().reset_index()
    counts.columns = ["card_due", "count"]
    counts = full_range_df.merge(counts, on="card_due", how="left").fillna(0)
    counts["count"] = counts["count"].astype(int)
    fig = go.Figure([go.Bar(x=counts["count"], y=counts["card_due"], orientation="h", name="Due Cards")])

fig.update_layout(
    template=DASHBOARD_COLORS["dark"]["template"],
    paper_bgcolor=DASHBOARD_COLORS["dark"]["paper_bg"],
    plot_bgcolor=DASHBOARD_COLORS["dark"]["plot_bg"],
    font=dict(color=DASHBOARD_COLORS["dark"]["font"]),
    height=max(len(counts) * 20, 420),
    legend_title_text="List",
)
fig.update_xaxes(showticklabels=False, showgrid=False)
fig.update_yaxes(
    tickmode="array",
    tickvals=counts["card_due"],
    ticktext=counts["card_due"].dt.strftime("%d %b"),
    showgrid=True,
    gridcolor=DASHBOARD_COLORS["dark"]["grid"],
)
fig.update_yaxes(autorange="reversed")

annotations = []
max_val = max(counts.groupby("card_due")["count"].sum().max(), 1)
for _, row in counts.groupby("card_due")["count"].sum().reset_index().iterrows():
    annotations.append(
        {
            "x": max_val * 1.2,
            "y": row["card_due"],
            "text": str(int(row["count"])),
            "showarrow": False,
            "xanchor": "left",
            "font": {"color": DASHBOARD_COLORS["dark"]["font"]},
        }
    )

fig.update_layout(annotations=annotations)
st.plotly_chart(fig, use_container_width=True)
