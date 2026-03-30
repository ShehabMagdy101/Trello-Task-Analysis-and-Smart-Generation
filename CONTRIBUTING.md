# Contributing Guide

Thank you for your interest in improving **Trello Task Analysis & Smart Generation**.

This document explains how to contribute safely and efficiently.

## What is `CONTRIBUTING.md`?

`CONTRIBUTING.md` is the contributor playbook for an open-source project. It tells contributors:

- how to set up the project locally,
- how to propose changes,
- coding/documentation expectations,
- how pull requests are reviewed and merged.

Having this file makes contribution and forking smoother and reduces back-and-forth in reviews.

## Prerequisites

- Python 3.10+
- A GitHub account
- Trello API key/token and board ID
- Google API key (Gemini)

## 1) Fork and clone

1. Fork the repository on GitHub.
2. Clone your fork:

```bash
git clone https://github.com/<your-username>/Trello-Task-Analysis-and-Smart-Generation.git
cd Trello-Task-Analysis-and-Smart-Generation
```

## 2) Create a local environment

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Configure secrets

Create `app.env` in repo root:

```env
TRELLO_API_KEY=your_trello_api_key
TRELLO_API_TOKEN=your_trello_api_token
BOARD_ID=your_trello_board_id
GOOGLE_API_KEY=your_google_ai_api_key
```

> Never commit `app.env` or credentials.

## 4) Run locally

```bash
python fetch_trello_data.py
streamlit run app.py
```

## 5) Branch naming and commit style

Create focused branches:

- `feat/<short-topic>` for new features
- `fix/<short-topic>` for bug fixes
- `docs/<short-topic>` for docs only
- `refactor/<short-topic>` for internal code improvements

Use clear commit messages, for example:

- `feat: add fallback for missing due dates`
- `fix: handle Trello API non-200 responses`
- `docs: improve setup instructions`

## 6) Pull request checklist

Before opening a PR, ensure:

- [ ] Change is scoped and focused.
- [ ] README/docs are updated if behavior changed.
- [ ] You tested your change locally.
- [ ] Secrets were not added to commits.

PR description should include:

1. Problem statement
2. What changed
3. How to test
4. Screenshots for UI changes

## 7) Code quality expectations

- Prefer small, reviewable PRs.
- Keep functions single-purpose.
- Add/adjust docstrings and comments where useful.
- Handle API/network failures explicitly where possible.

## 8) Reporting bugs and requesting features

Please open an issue with:

- expected behavior,
- actual behavior,
- reproduction steps,
- environment details (OS, Python version),
- screenshots/logs when relevant.

## 9) Review and merge process

- Maintainers review PRs and may request changes.
- Once approved, a maintainer merges.
- If your PR touches behavior, include docs updates in the same PR.

---

Thanks again for contributing 🚀
