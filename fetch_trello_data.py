import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from config import settings
from dotenv import dotenv_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env_values = dotenv_values("./app.env")

APIKey = env_values['TRELLO_API_KEY']
APIToken = env_values['TRELLO_API_TOKEN']
Board_ID = env_values['BOARD_ID']

query = {
  'key': APIKey,
  'token': APIToken
}

BASE_URL = f"https://api.trello.com/1/boards/{Board_ID}"
url_cards = f"{BASE_URL}/cards"
url_lists = f"{BASE_URL}/lists"

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

current_lists_ids = []
lists = response_lists.json()
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

DONE_LIST_NAME = settings.DONE_LIST_NAME

# add columns
data["status"] = "Not Done"
data["done_date"] = pd.NaT
data['origin_list'] = None

# Get all actions in one API call
BOARD_ACTIONS_URL = f"https://api.trello.com/1/boards/{Board_ID}/actions"

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


data['status'] = 'Not Done'  # default
done_mask = data['card_id'].isin(done_transitions.keys())

# Update only the relevant rows
data.loc[done_mask, 'status'] = 'Done'
data.loc[done_mask, 'done_date'] = data.loc[done_mask, 'card_id'].map(
    lambda x: pd.to_datetime(done_transitions[x]['done_date']).tz_convert(None)
)
data.loc[done_mask, 'origin_list'] = data.loc[done_mask, 'card_id'].map(
    lambda x: done_transitions[x]['origin_list']
)


undone_df = data[data['status'] == 'Not Done'][["list", "card", "card_due", "card_age"]]

undone_df['card_due'] = pd.to_datetime(undone_df['card_due'], errors='coerce')
today = pd.Timestamp.now(tz='UTC')
undone_df['overdue'] = undone_df['card_due'].lt(today)

undone_df['age_score'] = (undone_df['card_age'] / undone_df['card_age'].max()).round(2)

list_weights = settings.LIST_WEIGHTS

undone_df['list_weight'] = undone_df['list'].map(list_weights).fillna(settings.DEFAULT_LIST_SCORE)

undone_df['impact_score'] = (undone_df['age_score'] * undone_df['list_weight']).round(2)
undone_df['priority_score'] = (undone_df['impact_score'] + undone_df['overdue'].astype(int)).round(2)

# sort tasks by priority
undone_df = undone_df.sort_values('priority_score', ascending=False)

# save dataset
undone_df.to_csv(str(settings.UNDONE_DATA_PATH), index=False, encoding="utf-8")

data['done_date'] = pd.to_datetime(data['done_date'], utc=True)
cutoff = pd.Timestamp(settings.START_DATE, tz="UTC")
df_done_cutoff = data[(data['status'] == 'Done') & (data['done_date'] >= cutoff)].copy()

# save done tasks

df_done_cutoff.to_csv(str(settings.DONE_DATA_PATH))

df_full = data.copy()  # or use df_done_cutoff if you want only filtered Done tasks
df_full.to_csv(str(settings.ALL_DATA_PATH), index=False, encoding="utf-8")

logger.info("Fetching Tasks is Done!")