import pandas as pd
from config import settings
import streamlit as st

df = pd.read_csv(str(settings.ALL_DATA_PATH))
st.title("Dataset")
st.dataframe(df)
