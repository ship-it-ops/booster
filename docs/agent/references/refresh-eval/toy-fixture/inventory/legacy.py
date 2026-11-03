"""Loader for the pre-2024 CSV export. Kept until the export is archived."""

import csv
from pathlib import Path

LEGACY_FILE = Path(__file__).resolve().parent.parent / "data" / "legacy.csv"


def load_legacy():
    with LEGACY_FILE.open(newline="") as handle:
        return [{"sku": row["sku"], "qty": int(row["qty"])} for row in csv.DictReader(handle)]
