from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3

from .api.routes import router as api_router
from .db.connection import db_dependency, init_db
from .db import queries
from .render.renderer import render_citation

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parents[1]
TEMPLATES_DIR = BASE_DIR / "web" / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app = FastAPI(title="histy-server")
app.include_router(api_router)
app.mount("/ressources", StaticFiles(directory=str(ROOT_DIR / "ressources")), name="ressources")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> Any:
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/sources", response_class=HTMLResponse)
def sources_list(
    request: Request,
    q: str | None = None,
    conn: sqlite3.Connection = Depends(db_dependency),
) -> Any:
    query = q or ""
    items = queries.search_sources(conn, query, 200) if query else []
    return templates.TemplateResponse(
        "sources.html", {"request": request, "items": items, "q": query}
    )


@app.get("/sources/new", response_class=HTMLResponse)
def sources_new(request: Request) -> Any:
    return templates.TemplateResponse("sources_edit.html", {"request": request, "source": {}})


@app.post("/sources/new")
def sources_create(
    request: Request,
    source_type: str = Form(...),
    title: str = Form(...),
    short_title: str | None = Form(None),
    year: str | None = Form(None),
    place: str | None = Form(None),
    publisher: str | None = Form(None),
    container_title: str | None = Form(None),
    volume: str | None = Form(None),
    issue: str | None = Form(None),
    pages: str | None = Form(None),
    url: str | None = Form(None),
    accessed: str | None = Form(None),
    archive_name: str | None = Form(None),
    collection: str | None = Form(None),
    signature: str | None = Form(None),
    folio: str | None = Form(None),
    contributor_name: str | None = Form(None),
    contributor_role: str | None = Form(None),
    conn: sqlite3.Connection = Depends(db_dependency),
) -> Any:
    contributors = []
    if contributor_name:
        contributors.append(
            {"name": contributor_name, "role": contributor_role or "author", "is_corporate": False}
        )

    payload = {
        "type": source_type,
        "title": title,
        "short_title": short_title,
        "year": year,
        "place": place,
        "publisher": publisher,
        "container_title": container_title,
        "volume": volume,
        "issue": issue,
        "pages": pages,
        "url": url,
        "accessed": accessed,
        "archive_name": archive_name,
        "collection": collection,
        "signature": signature,
        "folio": folio,
        "contributors": contributors,
    }
    queries.upsert_source(conn, payload)
    return RedirectResponse("/sources", status_code=303)


@app.get("/sources/{source_id}", response_class=HTMLResponse)
def sources_edit(
    request: Request, source_id: str, conn: sqlite3.Connection = Depends(db_dependency)
) -> Any:
    source = queries.get_source(conn, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="source_not_found")
    return templates.TemplateResponse(
        "sources_edit.html", {"request": request, "source": source}
    )


@app.post("/sources/{source_id}")
def sources_update(
    request: Request,
    source_id: str,
    source_type: str = Form(...),
    title: str = Form(...),
    short_title: str | None = Form(None),
    year: str | None = Form(None),
    place: str | None = Form(None),
    publisher: str | None = Form(None),
    container_title: str | None = Form(None),
    volume: str | None = Form(None),
    issue: str | None = Form(None),
    pages: str | None = Form(None),
    url: str | None = Form(None),
    accessed: str | None = Form(None),
    archive_name: str | None = Form(None),
    collection: str | None = Form(None),
    signature: str | None = Form(None),
    folio: str | None = Form(None),
    contributor_name: str | None = Form(None),
    contributor_role: str | None = Form(None),
    conn: sqlite3.Connection = Depends(db_dependency),
) -> Any:
    contributors = []
    if contributor_name:
        contributors.append(
            {"name": contributor_name, "role": contributor_role or "author", "is_corporate": False}
        )

    payload = {
        "id": source_id,
        "type": source_type,
        "title": title,
        "short_title": short_title,
        "year": year,
        "place": place,
        "publisher": publisher,
        "container_title": container_title,
        "volume": volume,
        "issue": issue,
        "pages": pages,
        "url": url,
        "accessed": accessed,
        "archive_name": archive_name,
        "collection": collection,
        "signature": signature,
        "folio": folio,
        "contributors": contributors,
    }
    queries.upsert_source(conn, payload)
    return RedirectResponse(f"/sources/{source_id}", status_code=303)


@app.get("/styles", response_class=HTMLResponse)
def styles_list(request: Request, conn: sqlite3.Connection = Depends(db_dependency)) -> Any:
    items = queries.list_styles(conn)
    return templates.TemplateResponse(
        "styles.html", {"request": request, "items": items}
    )


@app.get("/styles/{style_id}", response_class=HTMLResponse)
def styles_view(
    request: Request, style_id: str, conn: sqlite3.Connection = Depends(db_dependency)
) -> Any:
    style = queries.get_style(conn, style_id)
    if not style:
        raise HTTPException(status_code=404, detail="style_not_found")
    return templates.TemplateResponse(
        "styles_view.html", {"request": request, "style": style}
    )


@app.get("/styles/{style_id}/edit-templates", response_class=HTMLResponse)
def styles_edit_templates(
    request: Request, style_id: str, conn: sqlite3.Connection = Depends(db_dependency)
) -> Any:
    style = queries.get_style(conn, style_id)
    if not style:
        raise HTTPException(status_code=404, detail="style_not_found")
    return templates.TemplateResponse(
        "styles_edit_templates.html", {"request": request, "style": style}
    )


@app.post("/styles/{style_id}/edit-templates")
async def styles_update_templates(
    request: Request,
    style_id: str,
    conn: sqlite3.Connection = Depends(db_dependency),
) -> Any:
    style = queries.get_style(conn, style_id)
    if not style:
        raise HTTPException(status_code=404, detail="style_not_found")

    data = await request.form()
    templates_payload = {k: v for k, v in data.items() if k.startswith("tpl_")}

    for key, markdown in templates_payload.items():
        template_key = key.replace("tpl_", "")
        conn.execute(
            "UPDATE style_templates SET markdown = ? WHERE style_id = ? AND key = ?;",
            (markdown, style_id, template_key),
        )
    conn.commit()
    return RedirectResponse(f"/styles/{style_id}", status_code=303)


@app.get("/preview", response_class=HTMLResponse)
def preview_get(request: Request, conn: sqlite3.Connection = Depends(db_dependency)) -> Any:
    sources = queries.search_sources(conn, "", 200)
    styles = queries.list_styles(conn)
    return templates.TemplateResponse(
        "preview.html",
        {"request": request, "sources": sources, "styles": styles, "output": None},
    )


@app.post("/preview", response_class=HTMLResponse)
def preview_post(
    request: Request,
    source_id: str = Form(...),
    style_id: str = Form(...),
    locator: str | None = Form(None),
    conn: sqlite3.Connection = Depends(db_dependency),
) -> Any:
    source = queries.get_source(conn, source_id)
    style = queries.get_style(conn, style_id)
    if not source or not style:
        raise HTTPException(status_code=404, detail="preview_data_missing")

    citation = {
        "citation_uuid": "preview",
        "doc_id": "preview",
        "source_id": source_id,
        "locator": locator,
        "note_type": None,
    }
    output = render_citation(
        citation,
        source,
        source.get("contributors", []),
        style,
        [],
    )

    sources = queries.search_sources(conn, "", 200)
    styles = queries.list_styles(conn)
    return templates.TemplateResponse(
        "preview.html",
        {
            "request": request,
            "sources": sources,
            "styles": styles,
            "output": output,
            "selected_source_id": source_id,
            "selected_style_id": style_id,
            "locator": locator,
        },
    )
