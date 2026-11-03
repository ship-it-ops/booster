from dataclasses import dataclass, field
from datetime import date


@dataclass
class Account:
    id: int
    name: str
    email: str


@dataclass
class Line:
    description: str
    quantity: int
    unit_cents: int


@dataclass
class Invoice:
    id: int
    account_id: int
    lines: list
    due: date
    status: str = "open"
    paid_cents: int = 0
    tax_cents: int = 0
    tags: list = field(default_factory=list)
