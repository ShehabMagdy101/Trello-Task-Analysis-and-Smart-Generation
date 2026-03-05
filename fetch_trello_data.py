import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from config import settings
from dotenv import dotenv_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env_values = dotenv_values("./app.env")

# secrets
APIKey = env_values['TRELLO_API_KEY']
APIToken = env_values['TRELLO_API_TOKEN']

# constants
Board_ID = env_values['BOARD_ID']
BASE_URL = f"https://api.trello.com/1/boards/{Board_ID}"
url_cards = f"{BASE_URL}/cards"
url_lists = f"{BASE_URL}/lists"
BOARD_ACTIONS_URL = f"{BASE_URL}/actions"
DONE_LIST_NAME = settings.DONE_LIST_NAME

query = {
  'key': APIKey,
  'token': APIToken
}

def calculate_card_age_days(date_last_activity: str) -> int:
    last_activity = datetime.fromisoformat(
        date_last_activity.replace("Z", "+00:00")
    )
    now = datetime.now(timezone.utc)

    return (now - last_activity).days


logger.info("Fetching Data..")

# get all cards
response_cards = requests.request(
   "GET",
   url_cards,
   params=query
)
cards = response_cards.json()

# get all lists
response_lists = requests.request(
   "GET",
   url_lists,
   params=query
)
lists = response_lists.json()

current_lists_ids = []
for list in lists:
    current_lists_ids.append(list['id'])

# lists and cards combined
list_map = {lst["id"]: lst["name"] for lst in lists}
list_data = []
for card in cards:
    list_data.append({
        "list": list_map.get(card["idList"], "Unknown List"),
        "card": card['name'],
        'card_id': card['id'],
        'card_due': card['due'],
        'card_age': calculate_card_age_days(card['dateLastActivity'])
        })    
    
data = pd.DataFrame(list_data) 

# add columns
data["status"] = "Not Done"
data["done_date"] = pd.NaT
data['origin_list'] = None

params = {
    **query,
    "filter": "updateCard:idList",  # only list moves
    "limit": 1000                   # increase if needed
}

response = requests.get(BOARD_ACTIONS_URL, params=params)
actions = response.json()
actions = sorted(actions, key=lambda x: x['date'])

done_transitions = {}
for action in actions:
    action_data = action.get("data", {})
    if action.get("type") != "updateCard":
        continue

    list_after = action_data.get("listAfter", {}).get("name")
    list_before = action_data.get("listBefore", {}).get("name")
    card_info = action_data.get("card", {})
    card_id = card_info.get("id")

    # Only consider first move from a non-Done list to Done
    if list_after == DONE_LIST_NAME and list_before != DONE_LIST_NAME and card_id not in done_transitions:
        origin_list = list_before if list_before in list_map.values() else "other"
        done_transitions[card_id] = {
            "origin_list": origin_list,
            "done_date": action["date"]
        }

done_mask = data['card_id'].isin(done_transitions.keys())

# Update only the relevant rows
data.loc[done_mask, 'status'] = 'Done'
data.loc[done_mask, 'done_date'] = data.loc[done_mask, 'card_id'].map(
    lambda x: pd.to_datetime(done_transitions[x]['done_date']).tz_convert(None)
)
data.loc[done_mask, 'origin_list'] = data.loc[done_mask, 'card_id'].map(
    lambda x: done_transitions[x]['origin_list']
)

# Save Raw Data
raw_data = data.to_csv(str(settings.RAW_DATA_PATH), index=False, encoding="utf-8")

logger.info("Fetching Tasks is Done!")


# Mark cards currently in Done list
# data.loc[data['list'] == DONE_LIST_NAME, 'status'] = 'Done'
# # create undone dataset
# undone_df = data[data['status'] == 'Not Done'][["list", "card", "card_due", "card_age"]]

# # Normalize timestamp
# undone_df['card_due'] = pd.to_datetime(undone_df['card_due'], errors='coerce')
# today = pd.Timestamp.now().normalize()  # tz-naive


# # # Task Priority Calculation
# # DAYS_PLAN = settings.DAYS_PLAN

# # DAYS_PLAN = {
# #         "Friday": {
# #             "main": "Carreer",
# #             "seconday": "Writing"
# #             },
# #         "Saturday": {
# #             "main":"Tech Study",
# #             "secondary": "Reading"
# #             },  
# #         "Sunday": {
# #             "main":"علوم شرعية",
# #             "secondary": "work"
# #             },  
# #         "Monday": {
# #             "main":"Tech Study",
# #             "secondary": "Tech Projects"
# #             },           
# #         "Tuesday": {
# #             "main":"Tech Projects",
# #             "secondary": "Tech Study"
# #             },
# #         "Wednesday": {
# #             "main":"House Chores",
# #             "secondary": "Reading"
# #             },
# #         "Thursday": {
# #             "main":"Tech Study",
# #             "secondary": "Tech Projects"
# #             },    
# #     }

# def due_score(days):
#     if pd.isna(days):
#         return 0
#     if days < 0:
#         return 3 + abs(days) * 0.2  # overdue escalation
#     if days <= 2:
#         return 2.5
#     if days <= 5:
#         return 1.5
#     if days <= 10:
#         return 0.7
#     return 0

# # def day_alignment(list_name):
# #     today_name = today.strftime("%A")
# #     day_config = DAYS_PLAN.get(today_name, {})
# #     if list_name == day_config.get("main"):
# #         return 2
# #     elif list_name == day_config.get("secondary"):
# #         return 1
# #     return 0


# undone_df['card_due'] = pd.to_datetime(undone_df['card_due'], errors='coerce')
# undone_df['days_to_due'] = (undone_df['card_due'] - today).dt.days
# undone_df['age_score'] = np.log1p(undone_df['card_age']) / 5
# # Apply due score
# undone_df['due_score'] = undone_df['days_to_due'].apply(due_score)

# # # Apply day alignment
# # undone_df['day_alignment'] = undone_df['list'].apply(day_alignment)

# # undone_df['priority_score'] = (
# #     #   4 * undone_df['note_score']      # highest
# #     + 3 * undone_df['due_score']       # second
# #     + 2 * undone_df['day_alignment']   # third
# #     + 1.5 * undone_df['age_score']     # fourth
# #     # + 1 * undone_df['list_weight']     # base importance
# # )

# # # sort tasks by priority
# # undone_df = undone_df.sort_values('priority_score', ascending=False)

# # save undone dataset
# undone_df.to_csv(str(settings.UNDONE_DATA_PATH), index=False, encoding="utf-8")

# # apply time cuttoff
# data['done_date'] = pd.to_datetime(data['done_date'], utc=True)
# cutoff = pd.Timestamp(settings.START_DATE, tz="UTC")
# df_done_cutoff = data[(data['status'] == 'Done') & (data['done_date'] >= cutoff)].copy()

# # save done dataset
# df_done_cutoff.to_csv(str(settings.DONE_DATA_PATH))

# # save all tasks dataset
# df_full = data.copy()
# df_full.to_csv(str(settings.ALL_DATA_PATH), index=False, encoding="utf-8")

# logger.info("Fetching Tasks is Done!")