import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from config import settings

# --- Load data ---
df = pd.read_csv(str(settings.ALL_DATA_PATH))


# --- Page title ---
st.title(" Trello Task Analysis Dashboard")


# --- Dataset view ---
st.subheader(" Dataset")
st.dataframe(df)

# --- Tasks per list ---
st.subheader(" Tasks per List")
task_counts = df['list'].value_counts()
st.bar_chart(task_counts)

# --- Date conversions ---
df['done_date'] = pd.to_datetime(df['done_date'], errors='coerce')
done_df = df[df['done'] == 'Yes'].copy()
done_df['done_day'] = done_df['done_date'].dt.date

# -----------------------------
#  Tasks Done Today
# -----------------------------
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

# -----------------------------
#  Weekly Productivity (Day of Week)
# -----------------------------
st.subheader("Weekly Productivity")

done_df['weekday'] = done_df['done_date'].dt.day_name()

weekly_summary = (
    done_df['weekday']
    .value_counts()
    .reindex(['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
    .fillna(0)
)

# Convert to DataFrame for Streamlit's bar chart
weekly_df = weekly_summary.reset_index()
weekly_df.columns = ['Day', 'Tasks Completed']
weekly_df = weekly_df.set_index('Day')

st.bar_chart(weekly_df)


st.subheader(" Progress Trend Over Time")
tasks_per_day = done_df['done_day'].value_counts().sort_index()
st.line_chart(tasks_per_day)

# Generate Tasks
from model import generate_daily_tasks
st.divider()
st.header("🤖 AI Daily Task Planner")

undone_df = pd.read_csv(str(settings.UNDONE_DATA_PATH)).copy()

if undone_df.empty:
    st.success("All tasks are completed")
else:

    col1, col2 = st.columns([3, 1])

    with col1:
        user_notes = st.text_area(
            "You Notes",
            height=100,
        )
    with col2:
        include_reasoning = st.checkbox(
            "Include detailed reasoning",
            value=False
        )

    st.write("")
    generate_button = st.button(
        "Generate My Daily Tasks",
        type='primary',
        use_container_width=True
    )

    if generate_button:
        with st.spinner("AI is planning your day..."):
            try:
                csv_data = undone_df[['list', 'card', 'card_due']].to_csv(index=False)
                result = generate_daily_tasks(
                    csv_data=csv_data,
                    user_notes=user_notes,
                    include_reasoning=include_reasoning
                )

               

                if include_reasoning and result.get('reasoning'):
                    st.subheader("Overall Strategy")
                    st.info(result['reasoning'])

                st.subheader("Today's Recommended Tasks")
                tasks = result.get('tasks', [])

                if tasks:
                        for task in tasks:
                            # Priority badge color
                            priority = task['priority'].lower()
                            if priority == 'high':
                                badge = "🔴"
                                color = "#ffebee"
                            elif priority == 'medium':
                                badge = "🟡"
                                color = "#fff9c4"
                            else:
                                badge = "🟢"
                                color = "#e8f5e9"

                             # Create expandable task card
                            with st.container():
                                col_order, col_content = st.columns([0.5, 9.5])
                                
                                with col_order:
                                    st.markdown(f"### {task['order']}")
                                
                                with col_content:
                                    with st.expander(
                                        f"{badge} **{task['card']}**",
                                        expanded=True
                                    ):
                                        st.markdown(f"**Priority:** `{task['priority'].upper()}`")
                                        st.markdown(f"**List:** {task['list']}")
                                        if include_reasoning:
                                            st.markdown(f"**Why now:** {task['reason']}")
                                        
                                
                                st.markdown("---")
            except Exception as e:
                    st.error(f"Error generating tasks: {str(e)}")
                    st.exception(e)