from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
import sqlite3

from .models import (
    CitationCreateRequest,
    DocumentUpsertRequest,
    RenderBibliographyRequest,
    RenderCitationRequest,
    RenderRefreshRequest,
    RenderSourcesListRequest,
    SourceSearchRequest,
    SourceUpsertRequest,
    StylePreviewRequest,
    ValidateDocumentRequest,
)
from ..db.connection import db_dependency
from ..db import queries
from ..render.renderer import render_bibliography_entry, render_citation

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/styles")
def list_styles(conn: sqlite3.Connection = Depends(db_dependency)) -> dict[str, list[dict]]:
    return {"items": queries.list_styles(conn)}


@router.get("/styles/{style_id}")
def get_style(style_id: str, conn: sqlite3.Connection = Depends(db_dependency)) -> dict:
    style = queries.get_style(conn, style_id)
    if not style:
        raise HTTPException(status_code=404, detail="style_not_found")
    return style


@router.post("/styles/{style_id}/preview")
def style_preview(
    style_id: str,
    payload: StylePreviewRequest,
    conn: sqlite3.Connection = Depends(db_dependency),
) -> dict:
    style = queries.get_style(conn, style_id)
    if not style:
        raise HTTPException(status_code=404, detail="style_not_found")

    source = queries.get_source(conn, payload.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="source_not_found")

    citation = {
        "citation_uuid": "preview",
        "doc_id": payload.doc_id or "preview",
        "source_id": payload.source_id,
        "locator": payload.locator,
        "note_type": None,
    }

    prior_citations = []
    if payload.doc_id:
        prior_citations = queries.list_citations_for_doc(conn, payload.doc_id)

    output = render_citation(
        citation,
        source,
        source.get("contributors", []),
        style,
        prior_citations,
    )
    return {
        "plain_text": output.plain_text,
        "runs": output.runs,
        "metadata": output.metadata,
    }


@router.post("/sources/search")
def source_search(
    payload: SourceSearchRequest, conn: sqlite3.Connection = Depends(db_dependency)
) -> dict:
    items = queries.search_sources(conn, payload.q, payload.limit)
    return {"items": items}


@router.post("/sources/upsert")
def source_upsert(
    payload: SourceUpsertRequest, conn: sqlite3.Connection = Depends(db_dependency)
) -> dict:
    source = queries.upsert_source(conn, payload.model_dump())
    return {"source": source}


@router.post("/documents/upsert")
def document_upsert(
    payload: DocumentUpsertRequest, conn: sqlite3.Connection = Depends(db_dependency)
) -> dict:
    try:
        doc = queries.upsert_document(conn, payload.model_dump())
    except ValueError:
        raise HTTPException(status_code=400, detail="doc_fingerprint_required")
    return {"document": doc}


@router.post("/citations/create")
def citation_create(
    payload: CitationCreateRequest, conn: sqlite3.Connection = Depends(db_dependency)
) -> dict:
    citation = queries.create_citation(conn, payload.model_dump())
    return {"citation": citation}


@router.post("/render/citation")
def render_single_citation(
    payload: RenderCitationRequest, conn: sqlite3.Connection = Depends(db_dependency)
) -> dict:
    citation = queries.get_citation(conn, payload.citation_uuid)
    if not citation:
        raise HTTPException(status_code=404, detail="citation_not_found")
    if citation["doc_id"] != payload.doc_id:
        raise HTTPException(status_code=400, detail="doc_id_mismatch")

    doc = conn.execute(
        "SELECT active_style_id FROM documents WHERE id = ?;",
        (payload.doc_id,),
    ).fetchone()
    if not doc:
        raise HTTPException(status_code=404, detail="document_not_found")

    style = queries.get_style(conn, doc["active_style_id"])
    if not style:
        raise HTTPException(status_code=404, detail="style_not_found")

    source = queries.get_source(conn, citation["source_id"])
    if not source:
        raise HTTPException(status_code=404, detail="source_not_found")

    all_citations = queries.list_citations_for_doc(conn, payload.doc_id)
    prior = []
    for item in all_citations:
        if item["citation_uuid"] == payload.citation_uuid:
            break
        prior.append(item)

    output = render_citation(
        citation, source, source.get("contributors", []), style, prior
    )

    return {
        "plain_text": output.plain_text,
        "runs": output.runs,
        "metadata": output.metadata,
        "style_version": style.get("version"),
    }


@router.post("/render/refresh")
def render_refresh(
    payload: RenderRefreshRequest, conn: sqlite3.Connection = Depends(db_dependency)
) -> dict:
    doc = conn.execute(
        "SELECT active_style_id FROM documents WHERE id = ?;",
        (payload.doc_id,),
    ).fetchone()
    if not doc:
        raise HTTPException(status_code=404, detail="document_not_found")

    style = queries.get_style(conn, doc["active_style_id"])
    if not style:
        raise HTTPException(status_code=404, detail="style_not_found")

    citations = queries.list_citations_for_doc(conn, payload.doc_id, payload.citation_uuids)
    outputs = []
    prior: list[dict] = []
    for citation in citations:
        source = queries.get_source(conn, citation["source_id"])
        if not source:
            continue
        output = render_citation(
            citation, source, source.get("contributors", []), style, prior
        )
        outputs.append(
            {
                "citation_uuid": citation["citation_uuid"],
                "plain_text": output.plain_text,
                "runs": output.runs,
                "metadata": output.metadata,
            }
        )
        prior.append(citation)

    return {"items": outputs, "style_version": style.get("version")}


@router.post("/render/bibliography")
def render_bibliography(
    payload: RenderBibliographyRequest, conn: sqlite3.Connection = Depends(db_dependency)
) -> dict:
    doc = conn.execute(
        "SELECT active_style_id FROM documents WHERE id = ?;",
        (payload.doc_id,),
    ).fetchone()
    if not doc:
        raise HTTPException(status_code=404, detail="document_not_found")

    style = queries.get_style(conn, doc["active_style_id"])
    if not style:
        raise HTTPException(status_code=404, detail="style_not_found")

    sources = queries.list_sources_for_doc(conn, payload.doc_id)
    items = []
    for source in sources:
        output = render_bibliography_entry(
            source, source.get("contributors", []), style
        )
        items.append(
            {
                "source_id": source.get("id"),
                "plain_text": output.plain_text,
                "runs": output.runs,
                "metadata": output.metadata,
            }
        )

    return {"items": items, "style_version": style.get("version")}


@router.post("/render/sourceslist")
def render_sources_list(
    payload: RenderSourcesListRequest, conn: sqlite3.Connection = Depends(db_dependency)
) -> dict:
    doc = conn.execute(
        "SELECT active_style_id FROM documents WHERE id = ?;",
        (payload.doc_id,),
    ).fetchone()
    if not doc:
        raise HTTPException(status_code=404, detail="document_not_found")

    style = queries.get_style(conn, doc["active_style_id"])
    if not style:
        raise HTTPException(status_code=404, detail="style_not_found")

    sources = queries.list_sources_for_doc(conn, payload.doc_id)
    primary_types = {"primary_classical", "archive"}
    filtered = [s for s in sources if s.get("type") in primary_types]
    items = []
    for source in filtered:
        output = render_bibliography_entry(
            source, source.get("contributors", []), style
        )
        items.append(
            {
                "source_id": source.get("id"),
                "plain_text": output.plain_text,
                "runs": output.runs,
                "metadata": output.metadata,
            }
        )

    return {"items": items, "style_version": style.get("version")}


@router.post("/validate/document")
def validate_document(
    payload: ValidateDocumentRequest, conn: sqlite3.Connection = Depends(db_dependency)
) -> dict:
    doc = conn.execute(
        "SELECT id FROM documents WHERE id = ?;",
        (payload.doc_id,),
    ).fetchone()
    if not doc:
        raise HTTPException(status_code=404, detail="document_not_found")

    issues = []
    citations = queries.list_citations_for_doc(conn, payload.doc_id)
    for citation in citations:
        source = conn.execute(
            "SELECT id FROM sources WHERE id = ?;",
            (citation["source_id"],),
        ).fetchone()
        if not source:
            issues.append(
                {
                    "citation_uuid": citation["citation_uuid"],
                    "error": "missing_source",
                }
            )

    return {"issues": issues}
