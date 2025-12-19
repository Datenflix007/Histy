# API

All endpoints return JSON and stable error codes via `detail` fields.

## Health

- `GET /api/health`

## Styles

- `GET /api/styles`
- `GET /api/styles/{style_id}`
- `POST /api/styles/{style_id}/preview` `{ source_id, locator?, doc_id? }`

## Sources

- `POST /api/sources/search` `{ q, limit }`
- `POST /api/sources/upsert` `{ source payload }`

## Documents

- `POST /api/documents/upsert` `{ doc_fingerprint, name?, active_style_id? }`

## Citations

- `POST /api/citations/create` `{ doc_id, source_id, locator?, note_type? }`

## Rendering

- `POST /api/render/citation` `{ citation_uuid, doc_id }`
- `POST /api/render/refresh` `{ doc_id, citation_uuids? }`
- `POST /api/render/bibliography` `{ doc_id }`
- `POST /api/render/sourceslist` `{ doc_id, grouping? }`

## Validation

- `POST /api/validate/document` `{ doc_id }`
