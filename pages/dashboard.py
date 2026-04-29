import pandas as pd
# import numpy as np
import plotly.graph_objects as go
from plotly_calplot import calplot
from config import settings
from dashboard_theme import DASHBOARD_COLORS
import streamlit as st
import plotly.express as px
from trello_client import update_card_due_date

st.set_page_config(
    page_title="Task Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv(settings.ALL_DATA_PATH)
    done_df = pd.read_csv(settings.DONE_DATA_PATH)
    pending_df = pd.read_csv(settings.PENDING_DATA_PATH)
    done_df['done_date'] = pd.to_datetime(done_df['done_date'], errors='coerce', utc=True)
    df['card_due'] = pd.to_datetime(df.get('card_due'), errors='coerce')

    return df, done_df, pending_df

df, done_df, pending_df = load_data()


start_date = pd.to_datetime(settings.START_DATE).date()
end_date = pd.Timestamp.today().date()

def compute_metrics(filtered_df):
    total = len(filtered_df)
    completed = len(filtered_df[filtered_df['status'] == 'Done'])
    pending = total - completed
    rate = (completed / total * 100) if total else 0

    return total, completed, pending, rate

total_tasks, completed_tasks, pending_tasks, completion_rate = compute_metrics(df)

st.title("📊 Task Analytics Dashboard")
st.caption(f"**Period:** {start_date} to {end_date}")

with st.expander("🔧 Update Trello Due Date (Remote)", expanded=False):
    pending_cards_df = (
        df[df["status"] == "Not Done"][["card", "card_id", "list", "card_due"]]
        .dropna(subset=["card_id"])
        .sort_values(by=["list", "card"])
    )

    if pending_cards_df.empty:
        st.info("No pending tasks with card IDs were found.")
    else:
        task_label_map = {
            f"{row.card} ({row.list})": row.card_id
            for row in pending_cards_df.itertuples(index=False)
        }
        selected_label = st.selectbox(
            "Choose pending task",
            options=list(task_label_map.keys()),
            key="due_update_task_selector"
        )
        selected_due = st.date_input(
            "New due date",
            value=pd.Timestamp.today().date(),
            key="due_update_date_input"
        )

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

col1, col2, col3= st.columns(3)

with col1:
    left,right = st.columns(2)
    with right:
        done_df['weekday'] = done_df['done_date'].dt.day_name()
        most_productive = done_df['weekday'].value_counts().idxmax()
        st.metric("Best Day",
                most_productive,
                border=True,
                width='content')

with col2:
    left, center, right = st.columns(3)

    with left:
        st.metric("Total", total_tasks,
            border=True,
            )
    with center:
        st.metric("Completed", completed_tasks,
              border=True
              )
    with right:
        st.metric("Pending", pending_tasks,
              border=True,
              )
    
with col3:
    days_in_period = (end_date - start_date).days + 1
    avg_daily = len(done_df) / days_in_period
    st.metric("Avg Tasks/Day", f"{avg_daily:.2f}",
              border=True,
              height='content',
              width='content')
    

st.divider()
left, right = st.columns([2, 2])

with left:
    
    task_counts = (
        df[df['status'] == 'Not Done']
        .groupby('list')
        .size()
        .reset_index(name='count')
    )

    fig = px.bar(
        task_counts,
        x='list',
        y='count',
        title='Not Done Tasks per List',
        height=350,
    )

    fig.update_layout(
        title_x=0.4,  
        margin=dict(l=20, r=20, t=50, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)

with right:

    daily_tasks = done_df.groupby(done_df['done_date'].dt.date).size()

    all_days = pd.date_range(start=start_date, end=end_date, freq='D').date
    daily_tasks = daily_tasks.reindex(all_days, fill_value=0)

    daily_df_chart = pd.DataFrame({
        'Date': daily_tasks.index,
        'Tasks Completed': daily_tasks.values
    })

    fig = px.line(
        daily_df_chart,
        x='Date',
        y='Tasks Completed',
        markers=False,
        line_shape='linear',
        title='Daily Progress',
    )

    fig.update_layout(
        title_x=0.45,  
        margin=dict(l=20, r=20, t=50, b=40)
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

st.divider()
left, right = st.columns([2, 2])

with right:

    fig = px.pie(
        task_counts,
        names='list',
        values='count',
        title='Not Done Percentage',
        hole=0.3,
        color_discrete_sequence=DASHBOARD_COLORS["categorical"]
    )
    fig.update_layout(
        title_x=0.3,  
    )

    fig.update_traces(textposition='inside', textinfo='percent')
    st.plotly_chart(fig, use_container_width=True)

with left:
    
    done_task_counts = done_df['origin_list'].value_counts().reset_index()
    done_task_counts.columns = ['origin_list', 'count']
    # st.dataframe(done_task_counts)
    done_task_counts = done_task_counts[done_task_counts['origin_list'] != 'other']
    fig = px.pie(
        done_task_counts,
        names='origin_list',
        values='count',
        title="Done Tasks by List",
        hole=0.3,
        color_discrete_sequence=DASHBOARD_COLORS["categorical"]
    )

    fig.update_layout(
        title_x=0.3,  
    )
    fig.update_traces(textposition='inside', textinfo='percent')
    st.plotly_chart(fig, use_container_width=True)

st.divider()
left, right = st.columns([2, 2])

with left:
        
    day_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday',
                'Thursday', 'Friday', 'Saturday']

    done_df['weekday'] = done_df['done_date'].dt.day_name()

    done_df['weekday'] = pd.Categorical(
        done_df['weekday'],
        categories=day_order,
        ordered=True
    )

    weekly_df = (
        done_df['weekday']
        .value_counts()
        .sort_index()
        .reset_index()
    )

    weekly_df.columns = ['Day', 'Tasks Completed']

    fig = px.bar(
        weekly_df,
        x='Day',
        y='Tasks Completed',
        color='Tasks Completed',
        color_continuous_scale=DASHBOARD_COLORS["continuous_scale"],
        text='Tasks Completed',
        title='Tasks-Day Distribution'
    )

    fig.update_traces(textposition='outside')
    fig.update_layout(showlegend=False, height=400)

    st.plotly_chart(fig, use_container_width=True)


with right:
    daily_tasks = done_df.groupby(done_df['done_date'].dt.date).size()
    all_days = pd.date_range(start=start_date, end=end_date, freq='D').date
    daily_tasks = daily_tasks.reindex(all_days, fill_value=0)

    cumulative_df = pd.DataFrame({
        'Date': daily_tasks.index,
        'Cumulative Tasks': daily_tasks.values.cumsum()
    })

    fig = px.area(
        cumulative_df,
        x='Date',
        y='Cumulative Tasks',
        line_shape='linear'
    )

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

incomplete_tasks = df[df['status'] == 'Not Done'].copy()
old_task_age = settings.OLD_TASK_AGE

incomplete_tasks['age_category'] = incomplete_tasks['card_age'].apply(
    lambda x: f'Old (>{old_task_age} days)' if x > old_task_age else f'New (≤{old_task_age} days)'
)

#  Tasks Done Today
st.subheader("Tasks Done Today")

now_utc = pd.Timestamp.now(tz="UTC")
start_today = now_utc.normalize()
end_today = start_today + pd.Timedelta(days=1)

done_today = done_df[
    (done_df['done_date'] >= start_today) &
    (done_df['done_date'] < end_today)
]

if not done_today.empty:
    st.success(f"You completed {len(done_today)} task(s) today")

    st.dataframe(
        done_today[['card', 'origin_list']].rename(columns={
            'card': 'Task Name',
            'origin_list': 'From List'
        }),
        use_container_width=True
    )
else:
    st.info("No tasks completed yet today")


st.subheader("Oldest Pending Task")

oldest_tasks = (
    incomplete_tasks
    .sort_values(by='card_age', ascending=False)
    [['card', 'card_age', 'list']]   # choose columns to show
    .head(5)
)

st.dataframe(oldest_tasks)

# stacked bar chart

day_order = ['Friday', 'Saturday','Sunday', 'Monday', 'Tuesday', 'Wednesday', 
             'Thursday' ]

# Extract weekday
done_df['weekday'] = done_df['done_date'].dt.day_name()

# Order weekdays
done_df['weekday'] = pd.Categorical(
    done_df['weekday'],
    categories=day_order,
    ordered=True
)

# Group by weekday AND list
weekly_df = (
    done_df [done_df['origin_list'] != 'other']
    .groupby(['weekday', 'origin_list'])
    .size()
    .reset_index(name='Tasks Completed')
    .sort_values('weekday')
)

# Create stacked bar chart
fig = px.bar(
    weekly_df,
    x='weekday',
    y='Tasks Completed',
    color='origin_list',  
    title='Tasks Completed per Day (Grouped by List)',
    text='Tasks Completed'
)

fig.update_layout(
    barmode='group',
    height=600
)

fig.update_traces(textposition='inside')

st.plotly_chart(fig, use_container_width=True)


def remove_timezones(str):
    return str.split()[0]

# done tasks heatmap

done_calplot_start_date = pd.to_datetime(settings.START_DATE).date()
done_calplot_end_date = pd.Timestamp.today().date()

done_df_calplot = done_df.copy()
done_df_calplot = done_df_calplot.dropna(subset=['done_date'])
done_df_calplot['done_date'] = done_df_calplot['done_date'].astype(str).apply(remove_timezones)
done_counts_df = done_df_calplot['done_date'].value_counts().reset_index()
done_counts_df.columns = ['done_date', 'count']
fig = calplot(
    done_counts_df,
    x="done_date",
    y="count",
    name="Done Tasks",
    dark_theme=True,
    title="Done Tasks Heatmap",
    # start_month= done_calplot_start_date.month,
    # end_month= done_calplot_end_date.month,
    # colorscale= "blues",
    month_lines= False,
)

fig.update_layout(
    title={
        'text': "Done Tasks Heatmap",
        'y':0.99,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'}
)

st.plotly_chart(fig, use_container_width=True)

# pending due dates heatmap
calplot_start_date = pd.Timestamp.now()
calplot_end_date = calplot_start_date + pd.Timedelta(days=60)

pending_df_calplot = pending_df.copy()

pending_df_calplot = pending_df_calplot.dropna(subset=['card_due'])
pending_df_calplot['card_due'] = pending_df_calplot['card_due'].astype(str).apply(remove_timezones)

counts_df = pending_df_calplot['card_due'].value_counts().reset_index()
counts_df.columns = ['card_due', 'count']
fig = calplot(
    counts_df,
    x="card_due",
    y="count",
    dark_theme=True,
    title="Pending Tasks Due Dates",
    colorscale=DASHBOARD_COLORS["heatmap_scale"],
    month_lines= False,
    start_month= calplot_start_date.month,
    end_month= calplot_end_date.month
)

fig.update_layout(
    title={
        'text': "Pending Tasks Due Dates",
        'y':0.99,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'}
)
st.plotly_chart(fig, use_container_width=False)

# Overdue tasks
st.subheader("Overdue Tasks")
today = pd.Timestamp.now(tz="UTC").normalize()
overdue_tasks = pending_df.copy()
overdue_tasks['card_due'] = pd.to_datetime(
    overdue_tasks['card_due'],
    errors='coerce',
    utc=True
)
overdue_tasks = overdue_tasks[overdue_tasks['card_due'] < today]
st.dataframe(overdue_tasks[['card', 'list', 'card_due']].rename(columns={
            'card': 'Task Name',
            'list': 'List',
            'card_due': 'Due Date'
            }),
            use_container_width=True)

# Tasks due today table
st.subheader("Tasks Due Today")

today_start = pd.Timestamp.now(tz="UTC").normalize()
today_end = today_start + pd.Timedelta(days=1)

pending_due_today = pending_df.copy()
pending_due_today['card_due'] = pd.to_datetime(
    pending_due_today['card_due'],
    errors='coerce',
    utc=True
)
pending_due_today = pending_due_today[
    (pending_due_today['card_due'] >= today_start) &
    (pending_due_today['card_due'] < today_end)
]

if not pending_due_today.empty:
    st.dataframe(
        pending_due_today[['card', 'list', 'card_due']]
        .rename(columns={
            'card': 'Task Name',
            'list': 'List',
            'card_due': 'Due Date'
        }),
        use_container_width=True
    )
else:
    st.info("No tasks are due today.")

st.subheader("Tasks Due Tommorow")
pending_due_tommorow = pending_df.copy()
pending_due_tommorow['card_due'] = pd.to_datetime(
    pending_due_tommorow['card_due'],
    errors='coerce',
    utc=True
)
tomorrow = today + pd.Timedelta(days=1)
tomorrow_end = tomorrow + pd.Timedelta(days=1)

pending_due_tommorow = pending_due_tommorow[
    pending_due_tommorow["card_due"].dt.date == (today + pd.Timedelta(days=1)).date()
]
st.dataframe(
        pending_due_tommorow[['card', 'list', 'card_due']]
        .rename(columns={
            'card': 'Task Name',
            'list': 'List',
            'card_due': 'Due Date'
        }),
        use_container_width=True
    )


df = pending_df.copy()
due_source_col = 'list' if 'list' in df.columns else None

df['card_due'] = pd.to_datetime(df['card_due'], errors='coerce').dt.tz_convert(None).dt.normalize()
df = df.dropna(subset=['card_due'])

start = pd.Timestamp.today().normalize()
end = start + pd.DateOffset(months=2)
full_range_df = pd.DataFrame({'card_due': pd.date_range(start=start, end=end, freq='D')})

if due_source_col:
    df[due_source_col] = df[due_source_col].fillna('Unknown')
    counts = (
        df.groupby(['card_due', due_source_col])
        .size()
        .reset_index(name='count')
    )
    counts = full_range_df.merge(counts, on='card_due', how='left')
    counts[due_source_col] = counts[due_source_col].fillna('No Due Cards')
    counts['count'] = counts['count'].fillna(0).astype(int)

    color_palette = DASHBOARD_COLORS["qualitative_fallback"]
    source_values = counts[due_source_col].dropna().unique()
    color_map = {
        source: color_palette[idx % len(color_palette)]
        for idx, source in enumerate(sorted(source_values))
    }

    fig = px.bar(
        counts,
        x='count',
        y='card_due',
        color=due_source_col,
        orientation='h',
        barmode='stack',
        color_discrete_map=color_map,
        labels={
            'count': 'Due Cards',
            'card_due': 'Due Date',
            due_source_col: 'List'
        },
        title='Pending Due Dates by List'
    )
else:
    counts = df.groupby('card_due').size().reset_index()
    counts.columns = ['card_due', 'count']
    counts = full_range_df.merge(counts, on='card_due', how='left').fillna(0)
    counts['count'] = counts['count'].astype(int)

    fig = go.Figure([
        go.Bar(
            x=counts['count'],
            y=counts['card_due'],
            orientation='h',
            name='Due Cards'
        )
    ])

fig.update_layout(
    template=DASHBOARD_COLORS["dark"]["template"],
    paper_bgcolor=DASHBOARD_COLORS["dark"]["paper_bg"],
    plot_bgcolor=DASHBOARD_COLORS["dark"]["plot_bg"],
    font=dict(color=DASHBOARD_COLORS["dark"]["font"]),
    height=len(counts) * 20,
    legend_title_text='List'
)

fig.update_xaxes(
    showticklabels=False,
    showgrid=False
)

fig.update_yaxes(
    tickmode='array',
    tickvals=counts['card_due'],
    ticktext=counts['card_due'].dt.strftime('%d %b'),
    showgrid=True,
    gridcolor=DASHBOARD_COLORS["dark"]["grid"]
)

# Reverse order (latest on top)
fig.update_yaxes(autorange="reversed")

annotations = []
max_val = max(counts.groupby('card_due')['count'].sum().max(), 1)

daily_totals = counts.groupby('card_due')['count'].sum().reset_index()
for _, row in daily_totals.iterrows():
    annotations.append(
        dict(
            x=max_val * 1.2,
            y=row['card_due'],
            text=str(int(row['count'])),
            showarrow=False,
            xanchor='left',
            font=dict(color=DASHBOARD_COLORS["dark"]["font"])
        )
    )

fig.update_layout(annotations=annotations)

st.plotly_chart(fig, use_container_width=True)
