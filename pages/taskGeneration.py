
import streamlit as st
import pandas as pd
from config import settings

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
            "Your Notes",
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