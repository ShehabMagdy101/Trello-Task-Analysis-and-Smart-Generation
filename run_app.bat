@echo off
cd /d "%~dp0"

REM Activate venv
if exist venv\Scripts\activate (
    call venv\Scripts\activate
)

REM Run fetch script
echo Fetching Trello data...
python -m src.application.data_pipeline.fetcher

REM Apply Processing
echo Processing data...
python -m src.application.data_pipeline.processor

REM Run streamlit app
echo Starting Streamlit app...
streamlit run app.py

pause
