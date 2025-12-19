# histy-server

Local FastAPI server for the histy MVP. This service owns the SQLite project DB, renders citations, and serves a small web UI.

## Setup

```powershell
cd histy-server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
$env:HISTY_DB_PATH = "C:\\path\\to\\histy.db"  # optional
uvicorn app.main:app --reload --port 8000
```

Open the UI at `http://localhost:8000`.

## Tests

```powershell
pytest
```
