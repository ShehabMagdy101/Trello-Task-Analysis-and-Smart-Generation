from datetime import date, datetime, time, timezone

import requests
from dotenv import dotenv_values
from pathlib import Path

# Try to find app.env in the project root
ROOT_DIR = Path(__file__).parent.parent.parent.parent
env_path = ROOT_DIR / "app.env"

env_values = dotenv_values(str(env_path) if env_path.exists() else "./app.env")
API_KEY = env_values.get("TRELLO_API_KEY")
API_TOKEN = env_values.get("TRELLO_API_TOKEN")


def update_card_due_date(card_id: str, due_date: date) -> None:
    """
    Update Trello card due date using Trello REST API.

    Raises ValueError for invalid configuration/input and RuntimeError for API failures.
    """
    if not API_KEY or not API_TOKEN:
        raise ValueError("Missing Trello API credentials in app.env")

    if not card_id:
        raise ValueError("Card ID is required")

    due_dt = datetime.combine(due_date, time(20, 59)).replace(tzinfo=timezone.utc)
    due_value = due_dt.isoformat().replace("+00:00", "Z")

    url = f"https://api.trello.com/1/cards/{card_id}"
    params = {
        "key": API_KEY,
        "token": API_TOKEN,
        "due": due_value,
    }

    response = requests.put(url, params=params, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(
            f"Trello API error ({response.status_code}): {response.text[:300]}"
        )
