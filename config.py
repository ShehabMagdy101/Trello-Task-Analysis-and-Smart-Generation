from pathlib import Path

class Settings():
    MODEL = "gemini-3-flash-preview"
    UNDONE_DATA_PATH = Path("./data/undone_trello_tasks.csv")
    ALL_DATA_PATH = Path("./data/all_trello_tasks.csv")
    START_DATE = "2025-10-05"
    DONE_LIST_NAME = "Done"
    
settings = Settings()