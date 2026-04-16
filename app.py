import streamlit as st
import subprocess
import sys

# side bar navigation
st.set_page_config(page_title='Smart Tasking', layout='wide')

pages = {
    "Pages": [
    st.Page(r".\pages\dataset.py", title="Dataset"),
    st.Page(r".\pages\dashboard.py", title="Dashboard"),
    st.Page(r".\pages\taskGeneration.py", title="Generate Tasks")
    ],
}

def refresh_data() -> None:
    """Run the same data refresh pipeline used in run_app.bat."""
    steps = [
        "fetch_trello_data.py",
        "data_processing.py",
    ]

    for script in steps:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            st.error(f"Failed while running {script}.")
            if result.stderr:
                st.code(result.stderr)
            return

    st.cache_data.clear()
    st.success("Data refreshed successfully. Reloading dashboard...")
    st.rerun()


refresh_col, _ = st.columns([1, 6])
with refresh_col:
    if st.button("🔄 Refresh Data", help="Fetch latest Trello data and reprocess datasets"):
        with st.spinner("Refreshing data..."):
            refresh_data()

pg = st.navigation(pages, position='top')
pg.run()