import logging
import pandas as pd
from config import settings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Loading Raw Dataset")
data = pd.read_csv(str(settings.RAW_DATA_PATH))
data.loc[data['list'] == settings.DONE_LIST_NAME, 'status'] = 'Done'
pending_df = data[data['status'] == 'Not Done'][["list", "card", "card_due", "card_age"]]

logger.info("Applying Data Processing")

# Normalize timestamp
data['done_date'] = pd.to_datetime(data['done_date'], utc=True)
pending_df['card_due'] = pd.to_datetime(pending_df['card_due'], errors='coerce')
today = pd.Timestamp.now(tz="UTC") # tz-aware

# Task Priority Calculation
pending_df['days_to_due'] = (pending_df['card_due'] - today).dt.days

pending_df['priority_score'] = (
    (pending_df['days_to_due'] + pending_df["card_age"]) / 100
)
pending_df  = pending_df.sort_values('priority_score', ascending=False)

# Apply Time Cuttoff
cutoff = pd.Timestamp(settings.START_DATE, tz="UTC")
df_done_cutoff = data[(data['status'] == 'Done') & (data['done_date'] >= cutoff)].copy()

logger.info("Saving Processed Dataset..")

# Save Done Dataset
df_done_cutoff.to_csv(str(settings.DONE_DATA_PATH), index=True, encoding="utf-8")

# Save Pending Dataset
pending_df.to_csv(str(settings.PENDING_DATA_PATH), index=True, encoding="utf-8")

# Save All Data
df_full = data.copy()
df_full.to_csv(str(settings.ALL_DATA_PATH), index=True, encoding="utf-8")

logger.info("Saved Sucessfully")


# print("Total rows:", len(data))
# print("Done rows:", (data['status'] == 'Done').sum())
# print("Done after cutoff:", len(df_done_cutoff))
# print("NaT done_date count:", data['done_date'].isna().sum())