#!/bin/bash

cd "$(dirname "$0")" || exit

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Fetching Trello data..."
python3 -m src.application.data_pipeline.fetcher

echo "Processing data..."
python3 -m src.application.data_pipeline.processor

echo "Starting Streamlit app..."
streamlit run app.py
