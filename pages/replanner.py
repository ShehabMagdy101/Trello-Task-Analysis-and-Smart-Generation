import pandas as pd
import streamlit as st

from config import settings
from replanner_model import generate_replan_dataset
from trello_client import update_card_due_date

st.set_page_config(layout="wide", page_title="AI Replanner")
st.header("🧠 AI Due-Date Replanner")
st.caption(
    "Generate a replanning dataset first, then apply due-date changes to Trello. "
    "Applied due times are standardized to 11:59 PM."
)

pending_df = pd.read_csv(str(settings.PENDING_DATA_PATH)).copy()
all_df = pd.read_csv(str(settings.ALL_DATA_PATH)).copy()

pending_with_ids = (
    all_df[all_df["status"] == "Not Done"]
    .merge(
        pending_df[["card", "list", "card_due", "card_age", "days_to_due", "priority_score"]],
        on=["card", "list", "card_due", "card_age"],
        how="left",
    )
    .drop_duplicates(subset=["card_id"])
)

if pending_with_ids.empty:
    st.info("No pending tasks found to replan.")
    st.stop()

provider = st.selectbox(
    "Model Provider",
    options=["gemini", "mistral"],
    help=(
        "Free-tier-friendly defaults are used:\n"
        "- Gemini: gemini-2.0-flash\n"
        "- Mistral: mistral-small-latest"
    ),
)

user_instruction = st.text_area(
    "Replanning instruction",
    placeholder=(
        "Examples:\n"
        "- shift all due tasks today and make today empty\n"
        "- clear the day 2026-04-20 from any tasks without deleting\n"
        "- move all Work list tasks due this week to next week"
    ),
    height=150,
)

generate_col, apply_col = st.columns(2)

with generate_col:
    generate_clicked = st.button("1) Generate Replanning Dataset", type="primary")

with apply_col:
    apply_clicked = st.button("2) Apply Dataset Changes to Trello")

if generate_clicked:
    if not user_instruction.strip():
        st.warning("Please provide a replanning instruction first.")
    else:
        with st.spinner("Generating replanning dataset..."):
            try:
                csv_data = pending_with_ids[
                    ["card_id", "list", "card", "card_due", "card_age", "days_to_due", "priority_score"]
                ].to_csv(index=False)
                result = generate_replan_dataset(
                    csv_data=csv_data,
                    user_instruction=user_instruction,
                    provider=provider,
                )

                dataset_df = pd.DataFrame(result.get("tasks_to_update", []))
                if dataset_df.empty:
                    st.info("Model returned no due-date changes.")
                else:
                    st.session_state["replanner_dataset"] = dataset_df
                    st.session_state["replanner_summary"] = result.get("summary", "")
            except Exception as exc:
                st.error(f"Failed to generate replanning dataset: {exc}")

if st.session_state.get("replanner_summary"):
    st.subheader("Plan Summary")
    st.write(st.session_state["replanner_summary"])

dataset_df = st.session_state.get("replanner_dataset")
if isinstance(dataset_df, pd.DataFrame) and not dataset_df.empty:
    st.subheader("Generated Replanning Dataset")
    st.dataframe(dataset_df, use_container_width=True)

if apply_clicked:
    dataset_df = st.session_state.get("replanner_dataset")
    if dataset_df is None or dataset_df.empty:
        st.warning("Generate the dataset first.")
    else:
        applied = 0
        errors: list[str] = []

        for row in dataset_df.itertuples(index=False):
            new_due = getattr(row, "new_due", None)
            card_id = getattr(row, "card_id", "")

            if not new_due or pd.isna(new_due):
                continue

            try:
                parsed_due = pd.to_datetime(new_due, errors="raise").date()
                update_card_due_date(str(card_id), parsed_due)
                applied += 1
            except Exception as exc:
                errors.append(f"{getattr(row, 'card', card_id)}: {exc}")

        if applied:
            st.success(
                f"Applied {applied} due-date update(s) to Trello. "
                "Use main Refresh Data button to sync local files."
            )
        if errors:
            st.error("Some updates failed:")
            for err in errors:
                st.write(f"- {err}")
