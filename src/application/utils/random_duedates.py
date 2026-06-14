import pandas as pd
import random
from datetime import datetime, timedelta
from src.core.config import settings

def assign_random_due_dates(tasks_df):
    for index, row in tasks_df.iterrows():
        if pd.isnull(row['card_due']):
            random_days = random.randint(1, 7)
            tasks_df.at[index, 'card_due'] = (datetime.now() + timedelta(days=random_days)).strftime('%Y-%m-%d')
    return tasks_df

if __name__ == "__main__":
    tasks = pd.read_csv(str(settings.PENDING_DATA_PATH))
    print(assign_random_due_dates(tasks).sample(5) if len(tasks) >= 5 else assign_random_due_dates(tasks))
