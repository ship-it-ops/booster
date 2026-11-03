-- migrations/0014_rename_customer_email.sql
BEGIN;
ALTER TABLE customers RENAME COLUMN email TO contact_email;
CREATE INDEX customers_contact_email_idx ON customers (contact_email);
ALTER TABLE customers ALTER COLUMN phone SET NOT NULL;
COMMIT;
