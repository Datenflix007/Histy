from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Iterable

from jinja2 import Environment, BaseLoader


@dataclass
class RenderOutput:
    plain_text: str
    runs: list[dict[str, Any]]
    metadata: dict[str, Any]


def _split_name(name: str) -> tuple[str, str]:
    if "," in name:
        surname, given = name.split(",", 1)
        return surname.strip(), given.strip()
    parts = name.strip().split()
    if len(parts) <= 1:
        return name.strip(), ""
    return parts[-1], " ".join(parts[:-1])


def _format_contributors(contributors: list[dict[str, Any]]) -> dict[str, str]:
    authors = [c for c in contributors if c.get("role") == "author"]
    editors = [c for c in contributors if c.get("role") == "editor"]
    primary = authors or editors or contributors

    names = []
    for contributor in primary:
        name = contributor.get("name") or ""
        names.append(name)

    full = "; ".join(names)
    first_name = names[0] if names else ""
    surname, given = _split_name(first_name) if first_name else ("", "")
    return {
        "full": full,
        "first_name": first_name,
        "surname": surname,
        "given": given,
    }


def _apply_small_caps(name: str, surname: str, given: str, enabled: bool) -> str:
    if not enabled or not name:
        return name
    if surname and given:
        return f"<sc>{surname}</sc>, {given}"
    return f"<sc>{name}</sc>"


def _context_from_source(
    source: dict[str, Any],
    contributors: list[dict[str, Any]],
    rules: dict[str, Any],
) -> dict[str, Any]:
    contrib = _format_contributors(contributors)
    surname_smallcaps = bool(rules.get("surname_smallcaps"))

    author_full = contrib["full"]
    author_sc = _apply_small_caps(
        author_full, contrib["surname"], contrib["given"], surname_smallcaps
    )
    short_title = source.get("short_title") or source.get("title") or ""

    title = source.get("title") or ""
    title_italic = f"*{title}*" if rules.get("title_italic") and title else title

    locator = source.get("locator")
    pages_prefix = rules.get("pages_prefix") or ""
    locator_prefix = pages_prefix + " " if pages_prefix else ""

    return {
        "author": author_full,
        "author_sc": author_sc,
        "author_surname": contrib["surname"],
        "title": title,
        "title_italic": title_italic,
        "short_title": short_title,
        "year": source.get("year") or "",
        "place": source.get("place") or "",
        "publisher": source.get("publisher") or "",
        "container_title": source.get("container_title") or "",
        "volume": source.get("volume") or "",
        "issue": source.get("issue") or "",
        "pages": source.get("pages") or "",
        "url": source.get("url") or "",
        "accessed": source.get("accessed") or "",
        "archive_name": source.get("archive_name") or "",
        "collection": source.get("collection") or "",
        "signature": source.get("signature") or "",
        "folio": source.get("folio") or "",
        "locator": locator or "",
        "locator_prefix": locator_prefix,
        "locator_block": f", {locator_prefix}{locator}" if locator else "",
    }


def _select_variant(
    citation: dict[str, Any],
    prior_citations: list[dict[str, Any]],
) -> str:
    if not prior_citations:
        return "first"

    last = prior_citations[-1]
    if (
        last.get("source_id") == citation.get("source_id")
        and last.get("locator") == citation.get("locator")
    ):
        return "ibid"

    seen_source = any(
        prior.get("source_id") == citation.get("source_id") for prior in prior_citations
    )
    return "short" if seen_source else "first"


def _template_key_for_style(style: dict[str, Any], source: dict[str, Any], variant: str) -> str:
    style_id = style.get("id")
    if variant == "ibid" and "footnote_ibid" in style.get("templates", {}):
        return "footnote_ibid"

    if style_id == "style-kmz":
        if source.get("type") == "primary_classical":
            return "footnote_primary_classical"
        return "footnote_literature_author_year"

    if variant == "short" and "footnote_short" in style.get("templates", {}):
        return "footnote_short"

    return "footnote_first"


def render_markdown_to_runs(markdown: str) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    if not markdown:
        return runs

    token_pattern = (
        r"(<sc>.*?</sc>|\*\*.*?\*\*|\*.*?\*|_.*?_)")
    import re

    parts = re.split(token_pattern, markdown)
    for part in parts:
        if not part:
            continue
        if part.startswith("<sc>") and part.endswith("</sc>"):
            text = part[4:-5]
            runs.append({"text": text, "small_caps": True})
        elif part.startswith("**") and part.endswith("**"):
            text = part[2:-2]
            runs.append({"text": text, "bold": True})
        elif (part.startswith("*") and part.endswith("*")) or (
            part.startswith("_") and part.endswith("_")
        ):
            text = part[1:-1]
            runs.append({"text": text, "italic": True})
        else:
            runs.append({"text": part})
    return runs


def _runs_to_plain_text(runs: list[dict[str, Any]]) -> str:
    return "".join(run.get("text", "") for run in runs)


def _render_template(markdown: str, context: dict[str, Any]) -> str:
    env = Environment(loader=BaseLoader(), autoescape=False)
    template = env.from_string(markdown)
    return template.render(**context)


def render_citation(
    citation: dict[str, Any],
    source: dict[str, Any],
    contributors: list[dict[str, Any]],
    style: dict[str, Any],
    prior_citations: list[dict[str, Any]],
) -> RenderOutput:
    rules = style.get("rules", {})
    variant = _select_variant(citation, prior_citations)
    template_key = _template_key_for_style(style, source, variant)
    template = style.get("templates", {}).get(template_key, "")

    context = _context_from_source(source, contributors, rules)
    context.update({
        "locator": citation.get("locator") or "",
        "locator_block": (
            f", {context['locator_prefix']}{citation.get('locator')}")
            if citation.get("locator")
            else "",
        "abbr": style.get("abbreviations", {}),
        "variant": variant,
    })

    markdown = _render_template(template, context).strip()
    runs = render_markdown_to_runs(markdown)
    plain_text = _runs_to_plain_text(runs).strip()

    render_hash = hashlib.sha256(
        f"{style.get('version')}::{template_key}::{markdown}".encode("utf-8")
    ).hexdigest()

    return RenderOutput(
        plain_text=plain_text,
        runs=runs,
        metadata={
            "variant": variant,
            "template_key": template_key,
            "render_hash": render_hash,
        },
    )


def render_bibliography_entry(
    source: dict[str, Any],
    contributors: list[dict[str, Any]],
    style: dict[str, Any],
) -> RenderOutput:
    rules = style.get("rules", {})
    template_key = "bibliography_entry"
    template = style.get("templates", {}).get(template_key, "")
    context = _context_from_source(source, contributors, rules)
    context.update({"abbr": style.get("abbreviations", {})})

    markdown = _render_template(template, context).strip()
    runs = render_markdown_to_runs(markdown)
    plain_text = _runs_to_plain_text(runs).strip()

    render_hash = hashlib.sha256(
        f"{style.get('version')}::{template_key}::{markdown}".encode("utf-8")
    ).hexdigest()

    return RenderOutput(
        plain_text=plain_text,
        runs=runs,
        metadata={
            "variant": "bibliography",
            "template_key": template_key,
            "render_hash": render_hash,
        },
    )
