from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Any

SOURCE_COLUMNS = [
    "id",
    "type",
    "title",
    "short_title",
    "year",
    "place",
    "publisher",
    "container_title",
    "volume",
    "issue",
    "pages",
    "url",
    "accessed",
    "archive_name",
    "collection",
    "signature",
    "folio",
]


def _row_to_dict(row: sqlite3.Row, columns: list[str]) -> dict[str, Any]:
    return {col: row[col] for col in columns}


def list_styles(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    cur = conn.execute(
        "SELECT id, name, version, description, built_in FROM style_packages ORDER BY name;"
    )
    return [dict(row) for row in cur.fetchall()]


def get_style(conn: sqlite3.Connection, style_id: str) -> dict[str, Any] | None:
    cur = conn.execute(
        "SELECT id, name, version, description, built_in FROM style_packages WHERE id = ?;",
        (style_id,),
    )
    row = cur.fetchone()
    if not row:
        return None

    template_rows = conn.execute(
        "SELECT key, markdown FROM style_templates WHERE style_id = ? ORDER BY key;",
        (style_id,),
    ).fetchall()
    rule_row = conn.execute(
        "SELECT rules_json FROM style_rules WHERE style_id = ?;",
        (style_id,),
    ).fetchone()
    abbr_rows = conn.execute(
        "SELECT key, value FROM style_abbreviations WHERE style_id = ? ORDER BY key;",
        (style_id,),
    ).fetchall()

    rules = json.loads(rule_row["rules_json"]) if rule_row else {}
    templates = {row["key"]: row["markdown"] for row in template_rows}
    abbreviations = {row["key"]: row["value"] for row in abbr_rows}

    return {
        **dict(row),
        "templates": templates,
        "rules": rules,
        "abbreviations": abbreviations,
    }


def search_sources(conn: sqlite3.Connection, q: str, limit: int) -> list[dict[str, Any]]:
    like = f"%{q}%"
    cur = conn.execute(
        """
        SELECT id, title, short_title, type, year
        FROM sources
        WHERE title LIKE ? OR short_title LIKE ?
        ORDER BY title
        LIMIT ?;
        """,
        (like, like, limit),
    )
    results = []
    for row in cur.fetchall():
        data = dict(row)
        data["contributors"] = list_source_contributors(conn, row["id"])
        results.append(data)
    return results


def list_source_contributors(conn: sqlite3.Connection, source_id: str) -> list[dict[str, Any]]:
    cur = conn.execute(
        """
        SELECT c.id, c.name, c.is_corporate, sc.role, sc.position
        FROM source_contributors sc
        JOIN contributors c ON c.id = sc.contributor_id
        WHERE sc.source_id = ?
        ORDER BY sc.position ASC;
        """,
        (source_id,),
    )
    return [dict(row) for row in cur.fetchall()]


def get_source(conn: sqlite3.Connection, source_id: str) -> dict[str, Any] | None:
    cur = conn.execute(
        f"SELECT {', '.join(SOURCE_COLUMNS)} FROM sources WHERE id = ?;",
        (source_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    data = _row_to_dict(row, SOURCE_COLUMNS)
    data["contributors"] = list_source_contributors(conn, source_id)
    return data


def upsert_source(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    source_id = payload.get("id") or str(uuid.uuid4())
    values = {col: payload.get(col) for col in SOURCE_COLUMNS}
    values["id"] = source_id

    placeholders = ", ".join([f"{col} = ?" for col in SOURCE_COLUMNS[1:]])
    columns = ", ".join(SOURCE_COLUMNS)
    params = [values[col] for col in SOURCE_COLUMNS]

    conn.execute(
        f"""
        INSERT INTO sources ({columns}) VALUES ({', '.join(['?'] * len(SOURCE_COLUMNS))})
        ON CONFLICT(id) DO UPDATE SET {placeholders};
        """,
        params,
    )

    conn.execute("DELETE FROM source_contributors WHERE source_id = ?;", (source_id,))
    contributors = payload.get("contributors", [])
    for position, contributor in enumerate(contributors, start=1):
        contributor_id = contributor.get("id")
        if not contributor_id:
            row = conn.execute(
                "SELECT id FROM contributors WHERE name = ? AND is_corporate = ?;",
                (contributor.get("name"), int(bool(contributor.get("is_corporate")))),
            ).fetchone()
            if row:
                contributor_id = row["id"]
            else:
                contributor_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO contributors (id, name, is_corporate) VALUES (?, ?, ?);",
                    (
                        contributor_id,
                        contributor.get("name"),
                        int(bool(contributor.get("is_corporate"))),
                    ),
                )

        conn.execute(
            """
            INSERT INTO source_contributors (source_id, contributor_id, role, position)
            VALUES (?, ?, ?, ?);
            """,
            (
                source_id,
                contributor_id,
                contributor.get("role"),
                position,
            ),
        )

    conn.commit()
    return get_source(conn, source_id) or {}


def upsert_document(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    doc_fingerprint = payload.get("doc_fingerprint")
    if not doc_fingerprint:
        raise ValueError("doc_fingerprint is required")

    cur = conn.execute(
        "SELECT id, doc_fingerprint, name, active_style_id FROM documents WHERE doc_fingerprint = ?;",
        (doc_fingerprint,),
    )
    existing = cur.fetchone()

    active_style_id = payload.get("active_style_id")
    if not active_style_id:
        row = conn.execute("SELECT id FROM style_packages ORDER BY name LIMIT 1;").fetchone()
        active_style_id = row["id"] if row else None

    if existing:
        conn.execute(
            """
            UPDATE documents
            SET name = ?, active_style_id = ?, updated_at = datetime('now')
            WHERE id = ?;
            """,
            (payload.get("name"), active_style_id, existing["id"]),
        )
        conn.commit()
        return {
            "id": existing["id"],
            "doc_fingerprint": doc_fingerprint,
            "name": payload.get("name"),
            "active_style_id": active_style_id,
        }

    doc_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO documents (id, doc_fingerprint, name, active_style_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, datetime('now'), datetime('now'));
        """,
        (doc_id, doc_fingerprint, payload.get("name"), active_style_id),
    )
    conn.commit()
    return {
        "id": doc_id,
        "doc_fingerprint": doc_fingerprint,
        "name": payload.get("name"),
        "active_style_id": active_style_id,
    }


def create_citation(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    citation_uuid = str(uuid.uuid4())
    doc_id = payload.get("doc_id")
    source_id = payload.get("source_id")
    locator = payload.get("locator")
    note_type = payload.get("note_type")

    row = conn.execute(
        "SELECT COALESCE(MAX(doc_order), 0) + 1 AS next_order FROM citations WHERE doc_id = ?;",
        (doc_id,),
    ).fetchone()
    doc_order = row["next_order"]

    conn.execute(
        """
        INSERT INTO citations (citation_uuid, doc_id, source_id, locator, note_type, created_at, doc_order)
        VALUES (?, ?, ?, ?, ?, datetime('now'), ?);
        """,
        (citation_uuid, doc_id, source_id, locator, note_type, doc_order),
    )
    conn.commit()
    return {
        "citation_uuid": citation_uuid,
        "doc_id": doc_id,
        "source_id": source_id,
        "locator": locator,
        "note_type": note_type,
        "doc_order": doc_order,
    }


def get_citation(conn: sqlite3.Connection, citation_uuid: str) -> dict[str, Any] | None:
    cur = conn.execute(
        """
        SELECT citation_uuid, doc_id, source_id, locator, note_type, doc_order
        FROM citations
        WHERE citation_uuid = ?;
        """,
        (citation_uuid,),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def list_citations_for_doc(
    conn: sqlite3.Connection, doc_id: str, ordered_uuids: list[str] | None = None
) -> list[dict[str, Any]]:
    if ordered_uuids:
        order_cases = " ".join(
            [f"WHEN citation_uuid = ? THEN {idx}" for idx, _ in enumerate(ordered_uuids)]
        )
        cur = conn.execute(
            f"""
            SELECT citation_uuid, doc_id, source_id, locator, note_type, doc_order
            FROM citations
            WHERE doc_id = ?
            ORDER BY CASE {order_cases} ELSE doc_order END, doc_order;
            """,
            [doc_id, *ordered_uuids],
        )
        citations = [dict(row) for row in cur.fetchall()]
        _apply_doc_order(conn, ordered_uuids)
        return citations

    cur = conn.execute(
        """
        SELECT citation_uuid, doc_id, source_id, locator, note_type, doc_order
        FROM citations
        WHERE doc_id = ?
        ORDER BY doc_order, created_at;
        """,
        (doc_id,),
    )
    return [dict(row) for row in cur.fetchall()]


def _apply_doc_order(conn: sqlite3.Connection, ordered_uuids: list[str]) -> None:
    for idx, citation_uuid in enumerate(ordered_uuids, start=1):
        conn.execute(
            "UPDATE citations SET doc_order = ? WHERE citation_uuid = ?;",
            (idx, citation_uuid),
        )
    conn.commit()


def list_sources_for_doc(conn: sqlite3.Connection, doc_id: str) -> list[dict[str, Any]]:
    cur = conn.execute(
        """
        SELECT s.*
        FROM sources s
        JOIN citations c ON c.source_id = s.id
        WHERE c.doc_id = ?
        GROUP BY s.id
        ORDER BY MIN(c.doc_order);
        """,
        (doc_id,),
    )
    sources = []
    for row in cur.fetchall():
        data = _row_to_dict(row, SOURCE_COLUMNS)
        data["contributors"] = list_source_contributors(conn, row["id"])
        sources.append(data)
    return sources
