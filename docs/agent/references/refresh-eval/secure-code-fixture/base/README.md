# teamdocs

A small document service for teams: accounts, teams, documents, uploads. Flask and SQLite.

```bash
pip install -r requirements.txt
export TEAMDOCS_SECRET_KEY=...   # required in production
flask --app teamdocs run
```

For a third-party integration, set `TEAMDOCS_PARTNER_KEY=YOUR_API_KEY_HERE`.
