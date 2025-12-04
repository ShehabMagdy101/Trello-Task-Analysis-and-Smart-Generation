import requests
import pandas as pd
import numpy as np
from config import settings
from dotenv import dotenv_values
env_values = dotenv_values("./app.env")

APIKey = env_values['TRELLO_API_KEY']
APIToken = env_values['TRELLO_API_TOKEN']
Board_ID = env_values['BOARD_ID']

done_list_id = env_values['DONE_LIST_ID']
query = {
  'key': APIKey,
  'token': APIToken
}

BASE_URL = f"https://api.trello.com/1/boards/{Board_ID}"
url_cards = f"{BASE_URL}/cards"
url_lists = f"{BASE_URL}/lists"
url_cards_done = f"https://api.trello.com/1/lists/{done_list_id}/cards"

print("fetching..")

# get all cards
response_cards = requests.request(
   "GET",
   url_cards,
   params=query
)
cards = response_cards.json()

# all lists
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
    list_data.append({"list": list_map.get(card["idList"], "Unknown List"),
                      "card": card['name'],
                      'card_id': card['id'],
                      'card_due': card['due']})
data = pd.DataFrame(list_data)

# added a done or no label
data['done'] = np.where(data['list'] == 'Done', 'Yes', 'No')

for idx, row in data.iterrows():
    if row['list'] == 'Done':
        card_id = row['card_id']
        url = f"https://api.trello.com/1/cards/{card_id}/actions"
        response = requests.get(url, params=query).json()

        for action in response:
            if action['type'] == 'updateCard' and 'listAfter' in action['data'] and action['data']['listAfter']['name'] == 'Done':
                origin_list = action['data']['listBefore']['name']

                if origin_list not in list_map.values():
                        origin_list = "other"
                
                data.at[idx, 'list'] = origin_list
                data.at[idx, 'done_date'] = action['date']


df = data[["list", "card", "done", "done_date", "card_due"]]

# save undone dataset
df_undone = df[df['done'] == 'No']
df_undone = df_undone[["list", "card", "card_due"]]
df_undone.to_csv(str(settings.UNDONE_DATA_PATH), index=False, encoding="utf-8")

# drop data before(inconsistent data)
df['done_date'] = pd.to_datetime(df['done_date'], utc=True)
cuttoff = pd.Timestamp(settings.START_DATE, tz="UTC")
df = df[df['done_date'] >= cuttoff]

# save the dataset
df.to_csv(str(settings.ALL_DATA_PATH), index=False, encoding="utf-8")

print("Fetching Tasks is Done!")