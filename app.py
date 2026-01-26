import streamlit as st
import pandas as pd
from config import settings

# side bar navigation
st.set_page_config(page_title='Smart Tasking', layout='wide')

pages = {
    "Pages": [
    st.Page(r"C:\Users\sheha\Desktop\Smart Tasking Project\pages\dataset.py", title="Dataset"),
    st.Page(r"C:\Users\sheha\Desktop\Smart Tasking Project\pages\dashboard.py", title="Dashboard"),
    st.Page(r"C:\Users\sheha\Desktop\Smart Tasking Project\pages\taskGeneration.py", title="Generate Tasks")
    ],
}

pg = st.navigation(pages, position='top')
pg.run()
