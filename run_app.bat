@echo off
cd /d "C:\Users\sheha\Desktop\Smart Tasking Project"

REM Activate venv
call venv\Scripts\activate

REM Run fetch script
python fetch_trello_data.py

REM Apply Processing
python data_processing.py

REM Run streamlit app
streamlit run app.py

pause
