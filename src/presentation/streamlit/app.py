import streamlit as st
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.application.data_pipeline.fetcher import fetch_data
from src.application.data_pipeline.processor import process_data

# side bar navigation
st.set_page_config(page_title='Smart Tasking', layout='wide')

pages = {
    "Pages": [
    # st.Page(r".\pages\dataset.py", title="Dataset"), # Missing in current pages/
    st.Page("pages/dashboard.py", title="Dashboard"),
    st.Page("pages/calendar.py", title="Calendar"),
    st.Page("pages/task_generator.py", title="Generate Tasks"),
    st.Page("pages/replanner.py", title="Replanner"),
    st.Page("pages/goals.py", title="Goals"),
    st.Page("pages/judger.py", title="Judger")
    ],
}

def refresh_data() -> None:
    """Run the same data refresh pipeline."""
    try:
        fetch_data()
        process_data()
        st.cache_data.clear()
        st.success("Data refreshed successfully. Reloading dashboard...")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to refresh data: {e}")


refresh_col, _ = st.columns([1, 6])
with refresh_col:
    if st.button("🔄 Refresh Data", help="Fetch latest Trello data and reprocess datasets"):
        with st.spinner("Refreshing data..."):
            refresh_data()

pg = st.navigation(pages, position='top')
pg.run()
