import pandas as pd
from config import settings
import streamlit as st
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(
    page_title="Task Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv(settings.ALL_DATA_PATH)
    done_df = pd.read_csv(settings.DONE_DATA_PATH)

    done_df['done_date'] = pd.to_datetime(done_df['done_date'], errors='coerce', utc=True)
    df['card_due'] = pd.to_datetime(df.get('card_due'), errors='coerce')

    return df, done_df

df, done_df = load_data()


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
        color_discrete_sequence=px.colors.cmocean.balance
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
        color_discrete_sequence=px.colors.cmocean.balance
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
        color_continuous_scale='Blues',
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
    # fig.update_traces(fill='tozeroy', line_color='#3584F3', fillcolor='rgba(149, 225, 211, 0.3)')
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