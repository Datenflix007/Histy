BEGIN;

CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  doc_fingerprint TEXT NOT NULL UNIQUE,
  name TEXT,
  active_style_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (active_style_id) REFERENCES style_packages(id)
);

CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  short_title TEXT,
  year TEXT,
  place TEXT,
  publisher TEXT,
  container_title TEXT,
  volume TEXT,
  issue TEXT,
  pages TEXT,
  url TEXT,
  accessed TEXT,
  archive_name TEXT,
  collection TEXT,
  signature TEXT,
  folio TEXT
);

CREATE TABLE IF NOT EXISTS contributors (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  is_corporate INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS source_contributors (
  source_id TEXT NOT NULL,
  contributor_id TEXT NOT NULL,
  role TEXT NOT NULL,
  position INTEGER NOT NULL,
  PRIMARY KEY (source_id, contributor_id, role),
  FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE,
  FOREIGN KEY (contributor_id) REFERENCES contributors(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS citations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  citation_uuid TEXT NOT NULL UNIQUE,
  doc_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  locator TEXT,
  note_type TEXT,
  created_at TEXT NOT NULL,
  doc_order INTEGER NOT NULL,
  FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE,
  FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS style_packages (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  version TEXT NOT NULL,
  description TEXT,
  built_in INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS style_templates (
  id TEXT PRIMARY KEY,
  style_id TEXT NOT NULL,
  key TEXT NOT NULL,
  markdown TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (style_id) REFERENCES style_packages(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS style_rules (
  id TEXT PRIMARY KEY,
  style_id TEXT NOT NULL,
  rules_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (style_id) REFERENCES style_packages(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS style_abbreviations (
  id TEXT PRIMARY KEY,
  style_id TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (style_id) REFERENCES style_packages(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sources_title ON sources(title);
CREATE INDEX IF NOT EXISTS idx_contributors_name ON contributors(name);
CREATE INDEX IF NOT EXISTS idx_citations_doc_id ON citations(doc_id);
CREATE INDEX IF NOT EXISTS idx_citations_source_id ON citations(source_id);
CREATE INDEX IF NOT EXISTS idx_style_templates_style_id ON style_templates(style_id);
CREATE INDEX IF NOT EXISTS idx_documents_fingerprint ON documents(doc_fingerprint);

COMMIT;
