from pathlib import Path
import markdown

ROOT_DIR = Path(__file__).parent.parent.parent

def user_goals(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        return f.read()

class Settings():
    MODEL = "gemini-3-flash-preview"
    DATA_DIR = ROOT_DIR / "Infrastructure" / "persistence" / "data"
    RAW_DATA_PATH = DATA_DIR / "raw" / "raw.csv"
    PENDING_DATA_PATH = DATA_DIR / "processed" / "pending.csv"
    ALL_DATA_PATH = DATA_DIR / "processed" / "full.csv"
    DONE_DATA_PATH = DATA_DIR / "processed" / "done.csv"
    START_DATE = "2025-10-05"
    DONE_LIST_NAME = "Done"
    OLD_TASK_AGE = 30
    GOALS = user_goals(ROOT_DIR / "goals.md")


settings = Settings()
