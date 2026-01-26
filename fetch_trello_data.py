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

done_transitions = {}

for action in actions:
    action_data = action.get("data", {})

    if (
        action_data.get("listAfter", {}).get("name") == DONE_LIST_NAME
        and action.get("type") == "updateCard"
    ):
        card_id = action_data["card"]["id"]

        # keep FIRST transition only
        if card_id not in done_transitions:
            done_transitions[card_id] = {
                "origin_list": action_data["listBefore"]["name"],
                "done_date": action["date"]
            }

for idx, row in data.iterrows():
    card_id = row["card_id"]

    if card_id in done_transitions:
        data.at[idx, "status"] = 'Done'
        data.at[idx, 'done_date'] = pd.to_datetime(done_transitions[card_id]['done_date']).tz_localize(None)
        data.at[idx, 'origin_list'] = done_transitions[card_id]['origin_list']

data[data["status"] == "Done"]["origin_list"].value_counts()
data["done_date"] = pd.to_datetime(data["done_date"])

df = data[['list', 'card','origin_list', 'card_age', 'card_due', 'status', 'done_date']]

# save undone dataset
df_undone = df[df['status'] == 'Not Done']
df_undone = df_undone[["list", "card", "card_due", "card_age"]]
df_undone.to_csv(str(settings.UNDONE_DATA_PATH), index=False, encoding="utf-8")

# drop data before specified date (inconsistent data)
df = df.copy()
df['done_date'] = pd.to_datetime(df['done_date'], utc=True)

# Apply cutoff
cutoff = pd.Timestamp(settings.START_DATE, tz="UTC")
df = df.loc[df['done_date'] >= cutoff].copy()

# save the full dataset
df.to_csv(str(settings.ALL_DATA_PATH), index=False, encoding="utf-8")

logger.info("Fetching Tasks is Done!")