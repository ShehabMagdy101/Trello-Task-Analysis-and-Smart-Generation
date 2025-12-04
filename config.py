from pathlib import Path

class Settings():
    MODEL = "gemini-2.5-flash-lite"
    UNDONE_DATA_PATH = Path("./data/undone_trello_tasks.csv")
    ALL_DATA_PATH = Path("./data/all_trello_tasks.csv")
    START_DATE = "2025-10-05"
settings = Settings()