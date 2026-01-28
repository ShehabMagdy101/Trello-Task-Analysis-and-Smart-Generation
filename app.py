import streamlit as st

# side bar navigation
st.set_page_config(page_title='Smart Tasking', layout='wide')

pages = {
    "Pages": [
    st.Page(r".\pages\dataset.py", title="Dataset"),
    st.Page(r".\pages\dashboard.py", title="Dashboard"),
    st.Page(r".\pages\taskGeneration.py", title="Generate Tasks")
    ],
}

pg = st.navigation(pages, position='top')
pg.run()