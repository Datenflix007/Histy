from __future__ import annotations

from app.db import queries


def test_search_sources(db_conn) -> None:
    results = queries.search_sources(db_conn, "Historia", 10)
    assert results
    assert results[0]["title"] == "Historia Regni"


def test_upsert_source(db_conn) -> None:
    payload = {
        "type": "monograph",
        "title": "Test Title",
        "year": "2024",
        "contributors": [{"name": "Doe, Jane", "role": "author", "is_corporate": False}],
    }
    source = queries.upsert_source(db_conn, payload)
    assert source["id"]
    fetched = queries.get_source(db_conn, source["id"])
    assert fetched
    assert fetched["title"] == "Test Title"
    assert fetched["contributors"][0]["name"] == "Doe, Jane"
