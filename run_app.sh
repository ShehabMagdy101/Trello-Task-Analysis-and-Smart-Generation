#!/bin/bash

cd "$(dirname "$0")" || exit

echo "Activating virtual environment..."
source venv/bin/activate

echo "Fetching Trello data..."
python3 fetch_trello_data.py

echo "Starting Streamlit app..."
streamlit run app.py
