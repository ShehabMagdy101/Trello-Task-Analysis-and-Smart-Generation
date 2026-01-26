import pandas as pd
from config import settings
import streamlit as st
import plotly.express as px

# --- Load data ---
df = pd.read_csv(str(settings.ALL_DATA_PATH))

# --- Page title ---
st.title("Dashboard")

# filter

st.sidebar.header("Time Filter")
time_option = st.sidebar.selectbox(
    "Show data for":
    ["All time", "Last 30 Days", "Last 7 Days", "Custom range"]
)

if time_option == "Last 7 Days":
# --- Tasks per list ---
task_counts = df['list'].value_counts().reset_index()
task_counts.columns = ['list', 'count']

fig = px.pie(
    task_counts,
    names='list',
    values='count',
    title='Tasks per List'
)

# fig.update_traces(textinfo='percent+value')
st.plotly_chart(fig, use_container_width=True)

# --- Date conversions ---
df['done_date'] = pd.to_datetime(df['done_date'], errors='coerce')
done_df = df[df['done'] == 'Yes'].copy()
done_df['done_day'] = done_df['done_date'].dt.date


#  Tasks Done Today

st.subheader("Tasks Done Today")

today = pd.Timestamp.now().normalize().date()
done_today = done_df[done_df['done_day'] == today]

if not done_today.empty:
    st.success(f" You completed {len(done_today)} task(s) today!")

    # Show as clean table
    st.dataframe(
        done_today[['card', 'list', 'card_due']].rename(columns={
            'card': 'Task Name',
            'list': 'From List',
            'card_due': 'Due Date'
        }),
        use_container_width=True
    )
else:
    st.info("No tasks completed yet today. Keep going 💪")


#  Weekly Productivity (Day of Week)

st.header("Tasks-Day Distribution")
day_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday',
             'Thursday', 'Friday', 'Saturday']

done_df['weekday'] = done_df['done_date'].dt.day_name()

# Make weekday ordered categorical
done_df['weekday'] = pd.Categorical(
    done_df['weekday'],
    categories=day_order,
    ordered=True
)

weekly_summary = done_df['weekday'].value_counts().sort_index()

weekly_df = weekly_summary.reset_index()
weekly_df.columns = ['Day', 'Tasks Completed']
weekly_df = weekly_df.set_index('Day')

st.bar_chart(weekly_df)

# Daily Progress

daily_tasks = (
    done_df
    .groupby(done_df['done_date'].dt.date)
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