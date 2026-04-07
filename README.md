# Notionsync

Python tool for syncing Google Calendar events and Canvas LMS assignments into Notion databases.

## What it does

- **canvaspull.py** — Pulls course assignments from the Canvas LMS API and syncs them to a Notion database
- **SyncgcaltoNotion.py** — Syncs Google Calendar events to Notion
- **sync.py** — Orchestrates the sync pipeline

## Setup

Requires a Notion integration token and Canvas API key. See `auth.py` for configuration.

```
pip install pipenv
pipenv install
pipenv run python sync.py
```

Built with Python, Notion API, Google Calendar API, and Canvas LMS API.
