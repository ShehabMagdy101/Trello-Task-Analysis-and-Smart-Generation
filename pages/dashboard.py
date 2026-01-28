import pandas as pd
from config import settings
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

# --- Page Configuration ---
st.set_page_config(
    page_title="Task Analytics Dashboard",
    page_icon="📊",
    layout="centered"
)

@st.cache_data
def load_data():
    df = pd.read_csv(settings.ALL_DATA_PATH)
    done_df = pd.read_csv(settings.DONE_DATA_PATH)

    done_df['done_date'] = pd.to_datetime(done_df['done_date'], errors='coerce', utc=True)
    df['card_due'] = pd.to_datetime(df.get('card_due'), errors='coerce')

    return df, done_df

df, done_df = load_data()


# ************** FILTERS ****************
st.sidebar.header("Filters")

# Time Filter
st.sidebar.subheader("Time Range")
time_option = st.sidebar.selectbox(
    "Select Period",
    ["All Time", "Last 7 days", "Last 30 days", "Last 90 days", "Custom"]
)

today = pd.Timestamp.now(tz="UTC").normalize()
if time_option == "Last 7 days":
    start_date = today - pd.Timedelta(days=7)
    end_date = today
elif time_option == "Last 30 days":
    start_date = today - pd.Timedelta(days=30)
    end_date = today
elif time_option == "Last 90 days":
    start_date = today - pd.Timedelta(days=90)
    end_date = today
elif time_option == "Custom":
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = pd.Timestamp(st.date_input("Start Date"), tz="UTC")
    with col2:
        end_date = pd.Timestamp(st.date_input("End Date"), tz="UTC")
else:
    start_date = pd.Timestamp(settings.START_DATE, tz="UTC")
    end_date = today


# List Filter
st.sidebar.subheader("Lists")
all_lists = df["list"].unique().tolist()
selected_lists = st.sidebar.multiselect(
    "Select Lists",
    options=all_lists,
    default=all_lists
)

# Task Status Filter
st.sidebar.subheader("Task Status")
status_filter = st.sidebar.radio(
    "Show Tasks",
    ["All Tasks", "Completed Only", "Incomplete Only"]
)

# Age Range Filter
st.sidebar.subheader("Task Age Range")
if not df['card_age'].isna().all():
    min_age = int(df['card_age'].min())
    max_age = int(df['card_age'].max())
    age_range = st.sidebar.slider(
        "Age (days)",
        min_value=min_age,
        max_value=max_age,
        value=(min_age, max_age)
    )
else:
    age_range = None

# ************** APPLY FILTERS ****************
def apply_filters(df, done_df, selected_lists, status_filter, age_range, start_date, end_date):
    fdf = df.copy()

    # List filter
    fdf = fdf[fdf['list'].isin(selected_lists)]

    # Status filter
    if status_filter == "Completed Only":
        fdf = fdf[fdf['status'] == 'Done']
    elif status_filter == "Incomplete Only":
        fdf = fdf[fdf['status'] == 'Not Done']

    # Age filter
    if age_range:
        fdf = fdf[(fdf['card_age'] >= age_range[0]) & (fdf['card_age'] <= age_range[1])]

    # Date filter for DONE tasks
    done_filtered = done_df[
        (done_df['done_date'] >= pd.Timestamp(start_date)) &
        (done_df['done_date'] <= pd.Timestamp(end_date))
    ]

    return fdf, done_filtered

filtered_df, done_filtered = apply_filters(
    df,
    done_df,
    selected_lists,
    status_filter,
    age_range,
    start_date,
    end_date
)

# ************** METRICS *****************

def compute_metrics(filtered_df):
    total = len(filtered_df)
    completed = len(filtered_df[filtered_df['status'] == 'Done'])
    pending = total - completed
    rate = (completed / total * 100) if total else 0

    return total, completed, pending, rate

total_tasks, completed_tasks, pending_tasks, completion_rate = compute_metrics(filtered_df)

# ************** DASHBOARD ****************

st.title("📊 Task Analytics Dashboard")
st.caption(f"**Period:** {start_date} to {end_date.date()}")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Tasks", total_tasks)

with col2:
    st.metric("Completed", completed_tasks, f"{completion_rate:.1f}%")

with col3:
    st.metric("Pending", pending_tasks)


st.subheader("Undone Tasks by List")
# --- Tasks per list ---
task_counts = (
    filtered_df[filtered_df['status'] == 'Not Done']
    .groupby('list')
    .size()
    .reset_index(name='count')
)

# st.dataframe(task_counts)

# drop 'Done' list
task_counts = task_counts.drop(0, inplace=False)

fig = px.pie(
    task_counts,
    names='list',
    values='count',
    # hole=0.3,
    # title='Undone tasks per List',
    # color_discrete_sequence=px.colors.qualitative.Set1
)

fig.update_traces(textposition='inside', textinfo='percent+label')
# fig.update_layout(showlegend=False, height=400)
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Done Tasks by List")
done_task_counts = done_filtered['origin_list'].value_counts().reset_index()
done_task_counts.columns = ['origin_list', 'count']
# st.dataframe(done_task_counts)
done_task_counts = done_task_counts[done_task_counts['origin_list'] != 'other']
fig = px.pie(
    done_task_counts,
    names='origin_list',
    values='count',
    # hole=0.3,
    # title='Undone tasks per List',
    # color_discrete_sequence=px.colors.qualitative.Set1
)
fig.update_traces(textposition='inside', textinfo='percent')
# fig.update_layout(showlegend=False, height=400)
st.plotly_chart(fig, use_container_width=True)



st.subheader("Task Age Distribution")
incomplete_tasks = filtered_df[filtered_df['status'] == 'Not Done'].copy()
fig = px.histogram(
    incomplete_tasks,
    x='card_age',
    nbins=30,
    labels={'card_age': 'Task Age (Days)', 'count': 'Number of Tasks'},
    color_discrete_sequence=['#FF6B6B']
)
fig.update_layout(
    showlegend=False,
    height=400,
    xaxis_title="Task Age (Days)",
    yaxis_title="Number of Tasks",
    bargap=0.1
)
st.plotly_chart(fig, use_container_width=True)

st.caption(f"📊 Stats: Min: {incomplete_tasks['card_age'].min():.0f} days | "
            f"Avg: {incomplete_tasks['card_age'].mean():.1f} days | "
            f"Max: {incomplete_tasks['card_age'].max():.0f} days")

st.subheader("New vs Old Tasks")

incomplete_tasks = filtered_df[filtered_df['status'] == 'Not Done'].copy()
old_task_age = settings.OLD_TASK_AGE

incomplete_tasks['age_category'] = incomplete_tasks['card_age'].apply(
    lambda x: f'Old (>{old_task_age} days)' if x > old_task_age else f'New (≤{old_task_age} days)'
)

selected_list_viz = st.selectbox(
    "Select List",
    options=["All Lists"] + selected_lists,
    key='old_new_list'
)

if selected_list_viz == "All Lists":
    list_age_data = incomplete_tasks.copy()
else:
    list_age_data = incomplete_tasks[incomplete_tasks['list'] == selected_list_viz]

if not list_age_data.empty:
    age_counts = list_age_data['age_category'].value_counts().reset_index()
    age_counts.columns = ['Age Category', 'Count']

    fig = px.pie(
        age_counts,
        names='Age Category',
        values='Count',
        color='Age Category',
        color_discrete_map={
            f'New (≤{old_task_age} days)': '#4ECDC4',
            f'Old (>{old_task_age} days)': '#F74E4E'
        }
    )

    fig.update_traces(textposition='inside', textinfo='percent+label+value')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    old_count = len(list_age_data[list_age_data['age_category'] == f'Old (>{old_task_age} days)'])
    new_count = len(list_age_data[list_age_data['age_category'] == f'New (≤{old_task_age} days)'])

    if selected_list_viz == "All Lists":
        st.caption(f"🌍 Overall: {old_count} old tasks, {new_count} new tasks")
    else:
        st.caption(f"📌 {selected_list_viz}: {old_count} old tasks, {new_count} new tasks")

else:
    st.info("No incomplete tasks in this selection")



st.divider()


#  Tasks Done Today
st.subheader("Tasks Done Today")

today = pd.Timestamp.now(tz="UTC").normalize()
done_today = done_df[done_df['done_date'] == today]

if not done_today.empty:
    st.success(f" You completed {len(done_today)} task(s) today")

    st.dataframe(
        done_today[['card', 'origin_list']].rename(columns={
            'card': 'Task Name',
            'list': 'From List',
        }),
        use_container_width=True
    )
else:
    st.info("No tasks completed yet today")

st.divider()


#  Weekly Productivity (Day of Week)

st.header("Tasks-Day Distribution")

day_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday',
             'Thursday', 'Friday', 'Saturday']

done_filtered['weekday'] = done_filtered['done_date'].dt.day_name()

done_filtered['weekday'] = pd.Categorical(
    done_filtered['weekday'],
    categories=day_order,
    ordered=True
)

weekly_df = (
    done_filtered['weekday']
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
    color_continuous_scale='Blues',
    text='Tasks Completed'
)

fig.update_traces(textposition='outside')
fig.update_layout(showlegend=False, height=400)

st.plotly_chart(fig, use_container_width=True)

# Daily Progress

daily_tasks = (
    done_filtered
    .groupby(done_filtered['done_date'].dt.date)
    .size()
)

start_date = pd.to_datetime(settings.START_DATE).date()
end_date = pd.Timestamp.today().date()

all_days = pd.date_range(
    start=start_date,
    end=end_date,
    freq='D'   
).date

daily_tasks = daily_tasks.reindex(all_days, fill_value=0)

daily_df = pd.DataFrame({
    'Date': daily_tasks.index,
    'Task Completed': daily_tasks.values
}).set_index('Date')

st.header("Daily Progress")
st.caption(f"Tracking from {start_date} to today")

st.line_chart(daily_df)

# Cumulative Progress

daily_df['Cumulative Tasks'] = daily_df['Task Completed'].cumsum()

st.header('Cumulative Progress')
st.caption(f"Tracking from {start_date} to today")
st.line_chart(daily_df[['Cumulative Tasks']])

st.divider()

daily_tasks = done_filtered.groupby(done_filtered['done_date'].dt.date).size()
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
fig.update_traces(fill='tozeroy', line_color='#95E1D3', fillcolor='rgba(149, 225, 211, 0.3)')
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)



daily_tasks = done_filtered.groupby(done_filtered['done_date'].dt.date).size()

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
    markers=True,
    line_shape='linear'
)
fig.update_traces(line_color='#4ECDC4', marker=dict(size=6))
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)


st.divider()

col1 , col2 = st.columns(2)

with col1:
    st.subheader("Average Daily Rate")
    days_in_period = (end_date - start_date).days + 1
    avg_daily = len(done_df) / days_in_period
    st.metric("Tasks/Day", f"{avg_daily:.2f}")

with col2:
    st.subheader("Most Productive Day")
    done_filtered['weekday'] = done_filtered['done_date'].dt.day_name()
    most_productive = done_filtered['weekday'].value_counts().idxmax()
    st.metric("Best Day", most_productive)


col1 , col2 = st.columns(2)


st.subheader("Oldest Pending Task")

oldest_tasks = (
    incomplete_tasks
    .sort_values(by='card_age', ascending=False)
    [['card', 'card_age', 'list']]   # choose columns to show
    .head(10)
)

st.dataframe(oldest_tasks)


