# Codebase Guide for New Contributors

This project is a **Streamlit-based productivity app** that:
1. Pulls task/card data from Trello.
2. Computes task analytics and priority-related metadata.
3. Uses an LLM (Gemini via LangChain) to generate a practical daily task plan.
4. Displays analytics and recommendations in a multi-page Streamlit UI.

## High-level architecture

The app is organized as a simple pipeline:

1. **Data ingestion (`fetcher.py`)**
   - Reads Trello credentials from `app.env`.
   - Calls Trello APIs for cards/lists/actions.
   - Builds a combined dataframe with:
     - task list name
     - card title
     - due date
     - card age
     - done/not done status
     - inferred origin list for done cards
   - Computes priority helper fields on not-done tasks (`age_score`, `list_weight`, `impact_score`, `priority_score`).
   - Writes CSV outputs used by the UI:
     - `data/all_trello_tasks.csv`
     - `data/done_tasks.csv`
     - `data/undone_trello_tasks.csv`

2. **LLM task planner (`model.py` + `prompt.py` + `output_format.py`)**
   - `prompt.py` defines system/user prompts as Pydantic models.
   - `output_format.py` defines the expected structured JSON output (`DailyTaskPlan`, `Task`).
   - `model.py` wires prompt + Gemini model + JSON parser in a LangChain chain.
   - `generate_daily_tasks(...)` is the main callable for producing today’s ordered tasks.

3. **UI (`app.py` + `pages/`)**
   - `app.py` creates top navigation and routes to pages.
   - `pages/dataset.py`: tabular data explorer.
   - `pages/dashboard.py`: analytics dashboard (KPIs and Plotly charts).
   - `pages/taskGeneration.py`: task-generation interface with user notes + optional reasoning.

4. **Run scripts (`run_app.sh`, `run_app.bat`)**
   - Activate venv.
   - Refresh Trello data.
   - Start Streamlit.

## Directory map

- `app.py`: Streamlit entrypoint and navigation.
- `src/application/data_pipeline/`: ETL and processing logic (`fetcher.py`, `processor.py`).
- `src/application/task_generation/`: LLM task-generation service and prompts.
- `src/application/replanning/`: LLM task-replanning service and prompts.
- `src/core/config.py`: Configurable constants and data paths.
- `src/presentation/streamlit/`: Streamlit app and pages.
- `Infrastructure/persistence/data/`: CSV data storage.
- `docs/`: Requirements and usage notes.
- `requirements.txt`: Dependency lock list.

## Important things to know before editing

1. **The app depends on `app.env` values**
   - Trello: `TRELLO_API_KEY`, `TRELLO_API_TOKEN`, `BOARD_ID`
   - Gemini: `GOOGLE_API_KEY`

2. **Data files are generated, not hand-written**
   - Most pages expect CSVs from `fetcher.py`.
   - If CSVs are stale/missing, dashboard and planner behavior can look broken.

3. **Scoring logic lives in one place**
   - Task prioritization helpers are calculated in `fetcher.py`.
   - List-based importance is configured in `config.py` (`LIST_WEIGHTS`).

4. **LLM output is schema-constrained**
   - The parser expects `tasks` (list) and optional `reasoning`.
   - UI components in `pages/taskGeneration.py` assume each task has `list`, `card`, `priority`, `order`, and `reason`.

5. **UI page config is duplicated in pages**
   - `app.py`, `pages/dashboard.py`, and `pages/taskGeneration.py` each call `st.set_page_config(...)`.
   - Streamlit usually expects this call once per app run, so this area is worth standardizing.

## Good “learn next” path for newcomers

1. **Read and run the data pipeline first**
   - Understand what CSV columns are produced and how they’re used downstream.

2. **Trace one full user flow**
   - `run_app.sh` -> `fetcher.py` output -> `pages/taskGeneration.py` -> `model.generate_daily_tasks()`.

3. **Study prompt/schema alignment**
   - Check that prompt instructions in `prompt.py` are consistent with fields required by `output_format.py`.

4. **Add guardrails and reliability checks**
   - Defensive handling for empty done history in dashboard metrics.
   - Better API error handling for Trello calls.

5. **Then improve product features**
   - Telegram integration (currently placeholder `telegram_bot.py`).
   - Confirmation/regeneration workflow mentioned in docs requirements.
   - Unit tests for scoring and transformation logic.

## Suggested first technical tasks

- Add tests for:
  - `calculate_card_age_days` and score calculations.
  - done-transition parsing from Trello actions.
- Refactor repeated page configuration into a single place.
- Add a lightweight “preflight” check page for env vars and data-file availability.
- Harden `fetcher.py` with explicit HTTP status checks and friendly error messages.

