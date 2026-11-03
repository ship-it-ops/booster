# Security conventions

- Every route that reads or changes a document goes through `@require_doc_access`, which checks that the document belongs to the caller's team.
- SQL goes through `db.query` / `db.execute` with `?` parameters. Identifiers (column names, sort order) are never taken from a request without an allowlist.
- No `shell=True`. External programs are run with an argument list.
- Secrets come from the environment. Nothing secret is logged.
- Uploaded files are served only from `UPLOAD_DIR`, by a name that has been through `safe_upload_path`.
