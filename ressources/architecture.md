# Architecture

histy is a local-first citation system with a single SQLite project database. The local FastAPI server is the sole authority for data and rendering logic. Word is a client that stores citation tokens and cached text.

## Components

- histy-server
  - SQLite database (sources, contributors, citations, documents, style packages)
  - Rendering engine (templates + rules -> runs)
  - REST API for Word add-in and web UI
  - Simple browser UI for data entry and preview

- histy-word
  - Office.js task pane
  - Inserts citations into footnotes
  - Stores tokens in Content Controls
  - Refreshes citations, bibliography, and sources list

## Token lifecycle

1. Add-in searches sources via /api/sources/search.
2. Add-in creates document and citation rows via /api/documents/upsert and /api/citations/create.
3. Add-in requests rendering via /api/render/citation.
4. Add-in inserts footnote + content control, storing a JSON token in the control tag.
5. Refresh enumerates tokens -> /api/render/refresh -> updates each footnote text and cached fields.

## Rendering decisions

Variant selection is deterministic:
- ibid if previous citation has same source_id and locator
- first if source not yet cited
- short otherwise

Templates and rules are stored in SQLite style packages. The renderer converts Markdown into run instructions (italic, bold, small caps) and returns plain_text for offline fallback.
