# Security conventions

- Projects belong to an organisation. Every route that reads or changes a project calls `load_project(project_id)`, which returns the project only if it belongs to the caller's organisation and aborts with 404 otherwise.
- SQL goes through `db.query` with `?` parameters.
