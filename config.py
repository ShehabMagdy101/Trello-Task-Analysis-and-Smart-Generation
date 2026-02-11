from pathlib import Path

class Settings():
    MODEL = "gemini-3-flash-preview"
    UNDONE_DATA_PATH = Path("./data/undone_trello_tasks.csv")
    ALL_DATA_PATH = Path("./data/all_trello_tasks.csv")
    DONE_DATA_PATH = Path("./data/done_tasks.csv")
    START_DATE = "2025-10-05"
    DONE_LIST_NAME = "Done"
    LIST_WEIGHTS = {
        "Tech Study": 1,
        "Tech Projects": 1,
        "علوم شرعية": 0.5,
        "Reading": 0.6,
        "Writing": 0.6,
        "Carreer": 0.8,
        "Planting": 0.5,
        "House Chores": 0.2,
        "Work": 0.4,
        "Fitness": 0.2
    }
    DEFAULT_LIST_SCORE = 0.5
    OLD_TASK_AGE = 30
    
settings = Settings()