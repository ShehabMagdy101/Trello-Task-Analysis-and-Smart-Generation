# logic
# fetch all tasks
# check due dates: if a task has no due date, assign a random one within the next 7 days

import pandas as pd
import random
from datetime import datetime, timedelta

tasks = pd.read_csv(r"C:\Users\sheha\Desktop\Smart Tasking Project\data\processed\pending.csv")

def assign_random_due_dates(tasks):
    for index, row in tasks.iterrows():
        if pd.isnull(row['card_due']):
            random_days = random.randint(1, 7)
            tasks.at[index, 'card_due'] = (datetime.now() + timedelta(days=random_days)).strftime('%Y-%m-%d')
    return tasks

# # Example usage
# tasks = [
#     {'name': 'Task 1', 'due_date': None},
#     {'name': 'Task 2', 'due_date': '2024-06-10'},
#     {'name': 'Task 3', 'due_date': None},
# ]

print(assign_random_due_dates(tasks).sample(random_state=42))