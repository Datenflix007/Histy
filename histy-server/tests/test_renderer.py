from __future__ import annotations

from app.render.renderer import render_citation


def test_variant_selection() -> None:
    style = {
        "id": "style-gs",
        "version": "1.0",
        "templates": {
            "footnote_first": "First",
            "footnote_short": "Short",
            "footnote_ibid": "Ibid",
        },
        "rules": {},
        "abbreviations": {},
    }
    source = {"id": "s1", "title": "Book"}
    contributors = []

    citation1 = {"citation_uuid": "c1", "source_id": "s1", "locator": "1"}
    out1 = render_citation(citation1, source, contributors, style, [])
    assert out1.metadata["variant"] == "first"

    citation2 = {"citation_uuid": "c2", "source_id": "s1", "locator": "2"}
    out2 = render_citation(citation2, source, contributors, style, [citation1])
    assert out2.metadata["variant"] == "short"

    citation3 = {"citation_uuid": "c3", "source_id": "s1", "locator": "2"}
    out3 = render_citation(citation3, source, contributors, style, [citation2])
    assert out3.metadata["variant"] == "ibid"


def test_template_substitution_and_runs() -> None:
    style = {
        "id": "style-gs",
        "version": "1.0",
        "templates": {
            "footnote_first": "{{ author_sc }}, {{ title_italic }}",
        },
        "rules": {"surname_smallcaps": True, "title_italic": True},
        "abbreviations": {},
    }
    source = {"id": "s1", "title": "Historia Regni"}
    contributors = [{"name": "Meyer, Anna", "role": "author"}]
    citation = {"citation_uuid": "c1", "source_id": "s1", "locator": "1"}

    output = render_citation(citation, source, contributors, style, [])
    assert "Historia Regni" in output.plain_text
    assert any(run.get("italic") for run in output.runs)
    assert any(run.get("small_caps") for run in output.runs)
