CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    total_cents BIGINT NOT NULL,
    status TEXT,
    legacy_status TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
