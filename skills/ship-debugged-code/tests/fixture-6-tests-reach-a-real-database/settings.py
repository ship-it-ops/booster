import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://app@db.staging.example.test:5432/orders")
