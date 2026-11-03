ALTER TABLE orders ADD COLUMN region TEXT NOT NULL;
ALTER TABLE orders DROP COLUMN legacy_status;
CREATE INDEX orders_customer_idx ON orders (customer_id);
