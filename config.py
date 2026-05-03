from pathlib import Path
import markdown

def user_goals(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        return f.read()

class Settings():
    MODEL = "gemini-3-flash-preview"
    RAW_DATA_PATH = Path("./data/raw/raw.csv")
    PENDING_DATA_PATH = Path("./data/processed/pending.csv")
    ALL_DATA_PATH = Path("./data/processed/full.csv")
    DONE_DATA_PATH = Path("./data/processed/done.csv")
    START_DATE = "2025-10-05"
    DONE_LIST_NAME = "Done"
    OLD_TASK_AGE = 30
    GOALS = user_goals("goals.md")


settings = Settings()