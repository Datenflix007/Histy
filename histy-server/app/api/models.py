from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SourceSearchRequest(BaseModel):
    q: str
    limit: int = Field(default=20, ge=1, le=100)


class ContributorIn(BaseModel):
    id: Optional[str] = None
    name: str
    role: str
    is_corporate: bool = False


class SourceUpsertRequest(BaseModel):
    id: Optional[str] = None
    type: str
    title: str
    short_title: Optional[str] = None
    year: Optional[str] = None
    place: Optional[str] = None
    publisher: Optional[str] = None
    container_title: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    url: Optional[str] = None
    accessed: Optional[str] = None
    archive_name: Optional[str] = None
    collection: Optional[str] = None
    signature: Optional[str] = None
    folio: Optional[str] = None
    contributors: list[ContributorIn] = Field(default_factory=list)


class DocumentUpsertRequest(BaseModel):
    doc_fingerprint: str
    name: Optional[str] = None
    active_style_id: Optional[str] = None


class CitationCreateRequest(BaseModel):
    doc_id: str
    source_id: str
    locator: Optional[str] = None
    note_type: Optional[str] = None


class RenderCitationRequest(BaseModel):
    citation_uuid: str
    doc_id: str


class RenderRefreshRequest(BaseModel):
    doc_id: str
    citation_uuids: Optional[list[str]] = None


class RenderBibliographyRequest(BaseModel):
    doc_id: str


class RenderSourcesListRequest(BaseModel):
    doc_id: str
    grouping: Optional[str] = None


class StylePreviewRequest(BaseModel):
    source_id: str
    locator: Optional[str] = None
    doc_id: Optional[str] = None


class ValidateDocumentRequest(BaseModel):
    doc_id: str
