# histy

Production-grade MVP for local-first citation management in Word.

## Structure

```
/
  histy-server/   # FastAPI server + SQLite + renderer + web UI
  histy-word/     # Word add-in (Office.js task pane)
  docs/           # Architecture + API docs
```

## Quick start

1) Start the server:

```powershell
cd histy-server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

2) Serve and sideload the Word add-in (see `histy-word/README.md`).

## Import the Word add-in

1) Serve the add-in UI (see `histy-word/README.md`) so `taskpane.html` is reachable at `https://localhost:3000`.
2) Open Word and go to **Insert > Add-ins > My Add-ins**.
3) Choose **Upload My Add-in** and select `histy-word/manifest.xml`.
4) Open the add-in from the **Home** tab and click **histy**.

## Notes

- The SQLite database is the single source of truth. Set `HISTY_DB_PATH` to choose where the DB file lives.
- Styles are stored in SQLite as style packages (templates + rules + abbreviations).
- Word stores citation tokens in content control tags with cached text for offline readability.

See `docs/architecture.md` and `docs/api.md` for details.
