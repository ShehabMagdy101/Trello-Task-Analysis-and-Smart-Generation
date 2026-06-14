import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from src.core.config import settings
from dotenv import dotenv_values
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to find app.env in the project root
ROOT_DIR = Path(__file__).parent.parent.parent.parent
env_path = ROOT_DIR / "app.env"
env_values = dotenv_values(str(env_path) if env_path.exists() else "./app.env")

# secrets
APIKey = env_values.get('TRELLO_API_KEY')
APIToken = env_values.get('TRELLO_API_TOKEN')
Board_ID = env_values.get('BOARD_ID')

if not all([APIKey, APIToken, Board_ID]):
    logger.error("Missing required Trello configuration in app.env")

# constants
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

def fetch_data():
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
    data.to_csv(str(settings.RAW_DATA_PATH), index=False, encoding="utf-8")

    logger.info("Fetching Tasks is Done!")

if __name__ == "__main__":
    fetch_data()
