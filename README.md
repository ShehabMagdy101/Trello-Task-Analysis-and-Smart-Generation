# Trello Task Analysis & Smart Generation

A Streamlit-based productivity tool that:

- Pulls task and activity data from a Trello board.
- Computes task analytics (age, completion history, list context).
- Uses Gemini (via LangChain) to generate a daily ordered task plan.
- Visualizes the dataset and analytics in a multi-page dashboard.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Run the App](#run-the-app)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

## Features

- **Trello ingestion** from cards, lists, and list-move actions.
- **Task status derivation** (done/not done + done date + inferred origin list).
- **LLM task planning** with structured output parsing.
- **Interactive Streamlit UI** with dataset explorer, dashboard, and task generation page.

## Architecture

1. **Data ingestion**: `fetch_trello_data.py`
   - Reads Trello API credentials from `app.env`.
   - Fetches cards/lists/actions and builds tabular task data.
   - Writes processed CSV files used by the UI.

2. **Task generation**: `model.py`, `prompt.py`, `output_format.py`
   - Sends context to Gemini through LangChain.
   - Enforces structured response formatting for generated plans.

3. **App UI**: `app.py` and `pages/`
   - Top-level navigation + pages for dataset, analytics, and plan generation.

## Prerequisites

- Python **3.10+** (recommended).
- A Trello account + board.
- Trello API credentials.
- Google AI API key for Gemini.

## Installation

```bash
git clone https://github.com/ShehabMagdy101/Trello-Task-Analysis-and-Smart-Generation.git
cd Trello-Task-Analysis-and-Smart-Generation

python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
# .venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
```

> If your environment has issues reading `requirements.txt` encoding, convert it to UTF-8 first or recreate a clean dependency file.

## Environment Variables

Create a file named `app.env` in the repository root:

```env
TRELLO_API_KEY=your_trello_api_key
TRELLO_API_TOKEN=your_trello_api_token
BOARD_ID=your_trello_board_id
GOOGLE_API_KEY=your_google_ai_api_key
MISTRAL_API_KEY=your_mistral_api_key
```

### How to get required values

- **TRELLO_API_KEY / TRELLO_API_TOKEN**:
  - Sign in to Trello and generate API credentials from Trello developer settings.
- **BOARD_ID**:
  - Open your Trello board and retrieve its board ID via API URL or board metadata.
- **GOOGLE_API_KEY**:
  - Create an API key in Google AI Studio / Google Cloud for Gemini access.

## Run the App

1. Fetch fresh Trello data:

```bash
python fetch_trello_data.py
```

2. Start Streamlit:

```bash
streamlit run app.py
```

3. Open the local URL shown in the terminal (usually `http://localhost:8501`).

4. (Optional) Update due dates remotely from the app:
   - Open **Dashboard** → **"🔧 Update Trello Due Date (Remote)"**.
   - Select a pending task, choose a date, and click update.
   - Refresh local CSVs:
   ```bash
   python fetch_trello_data.py
   python data_processing.py
   ```

## Project Structure

```text
.
├── app.py
├── config.py
├── fetch_trello_data.py
├── model.py
├── prompt.py
├── output_format.py
├── pages/
│   ├── dashboard.py
│   ├── dataset.py
│   └── taskGeneration.py
├── docs/
└── requirements.txt
```

## Configuration

Runtime constants (model name, data paths, scoring-related settings) are in `config.py`.

Examples:
- `MODEL`
- `RAW_DATA_PATH`
- `UNDONE_DATA_PATH`
- `DONE_LIST_NAME`

## Troubleshooting

### Missing `app.env` / key errors

- Ensure `app.env` exists at repo root.
- Confirm all required keys are present and non-empty.

### Trello API issues

- Verify API key/token validity.
- Confirm the board ID belongs to the same Trello workspace/account scope as the token.

### Streamlit page/config warnings

- Some Streamlit config can be duplicated across pages in current implementation.
- Consolidating page config is a good first refactor for contributors.

### Empty charts or no generated tasks

- Run `python fetch_trello_data.py` first.
- Confirm CSV outputs exist under configured `data/` paths.

## Roadmap

Planned improvements include:

- Better API/network error handling.
- Telegram integration completion.
- Confirmation/regeneration task workflow hardening.
- Automated tests and CI pipeline.

## Contributing

Contributions are welcome.

Recommended workflow:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feat/your-change`.
3. Make focused changes with clear commit messages.
4. Run local checks before opening a PR.
5. Open a Pull Request with:
   - Problem statement
   - Solution summary
   - Screenshots (for UI changes)
   - Testing notes

Please keep PRs small and easy to review.

## Security

- Never commit `app.env`, API keys, or tokens.
- Rotate credentials if accidentally exposed.
- Prefer least-privilege credentials where possible.

If you discover a security issue, please report it privately to the maintainers first.

## License

This project is licensed under the **Apache License 2.0**.

See the `LICENSE` file for details.
