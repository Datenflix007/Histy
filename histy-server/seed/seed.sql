BEGIN;

INSERT INTO style_packages (id, name, version, description, built_in, created_at)
VALUES
  ('style-gs', 'Germania Sacra (Richtlinien)', '1.0.0', 'MVP subset of GS rules.', 1, datetime('now')),
  ('style-kmz', 'Kurzes Merkblatt zum Zitieren', '1.0.0', 'MVP subset of KMZ rules.', 1, datetime('now'));

INSERT INTO style_templates (id, style_id, key, markdown, created_at)
VALUES
  ('tpl-gs-1', 'style-gs', 'footnote_first', '{{ author_sc }}, {{ title_italic }} ({{ place }}, {{ year }}){{ locator_block }}.', datetime('now')),
  ('tpl-gs-2', 'style-gs', 'footnote_short', '{{ author_sc }}, {{ short_title }}{{ locator_block }}.', datetime('now')),
  ('tpl-gs-3', 'style-gs', 'footnote_ibid', 'Ibid.{{ locator_block }}.', datetime('now')),
  ('tpl-gs-4', 'style-gs', 'bibliography_entry', '{{ author_sc }}, {{ title_italic }}. {{ place }} {{ year }}.', datetime('now')),

  ('tpl-kmz-1', 'style-kmz', 'footnote_primary_classical', '{{ author_sc }}, {{ title_italic }}{{ locator_block }}.', datetime('now')),
  ('tpl-kmz-2', 'style-kmz', 'footnote_literature_author_year', '{{ author_sc }}, {{ title_italic }} ({{ year }}){{ locator_block }}.', datetime('now')),
  ('tpl-kmz-3', 'style-kmz', 'footnote_ibid', 'Ibid.{{ locator_block }}.', datetime('now')),
  ('tpl-kmz-4', 'style-kmz', 'bibliography_entry', '{{ author_sc }}, {{ title_italic }}. {{ place }} {{ year }}.', datetime('now'));

INSERT INTO style_rules (id, style_id, rules_json, created_at)
VALUES
  ('rules-gs', 'style-gs', '{"surname_smallcaps": true, "title_italic": true, "pages_prefix": "S."}', datetime('now')),
  ('rules-kmz', 'style-kmz', '{"surname_smallcaps": false, "title_italic": true, "literature_footnote_mode": "author_year", "pages_prefix": "p."}', datetime('now'));

INSERT INTO style_abbreviations (id, style_id, key, value, created_at)
VALUES
  ('abbr-gs-1', 'style-gs', 'S.', 'S.', datetime('now')),
  ('abbr-gs-2', 'style-gs', 'Bd.', 'Bd.', datetime('now')),
  ('abbr-gs-3', 'style-gs', 'Hg.', 'Hg.', datetime('now')),
  ('abbr-gs-4', 'style-gs', 'Sp.', 'Sp.', datetime('now')),
  ('abbr-kmz-1', 'style-kmz', 'p.', 'p.', datetime('now')),
  ('abbr-kmz-2', 'style-kmz', 'vol.', 'vol.', datetime('now'));

INSERT INTO sources (id, type, title, short_title, year, place, publisher, container_title, volume, issue, pages, url, accessed, archive_name, collection, signature, folio)
VALUES
  ('source-001', 'monograph', 'Historia Regni', 'Historia Regni', '1850', 'Leipzig', 'Teubner', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
  ('source-002', 'primary_classical', 'Res Gestae', 'Res Gestae', '1st c.', 'Rome', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
  ('source-003', 'archive', 'Town Archive: Council Minutes', 'Council Minutes', '1620', 'Bremen', NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'Town Archive', 'Council Records', 'A-12', 'fol. 3r');

INSERT INTO contributors (id, name, is_corporate)
VALUES
  ('contrib-001', 'Meyer, Anna', 0),
  ('contrib-002', 'Augustus', 0),
  ('contrib-003', 'Town Archive', 1);

INSERT INTO source_contributors (source_id, contributor_id, role, position)
VALUES
  ('source-001', 'contrib-001', 'author', 1),
  ('source-002', 'contrib-002', 'author', 1),
  ('source-003', 'contrib-003', 'author', 1);

COMMIT;
