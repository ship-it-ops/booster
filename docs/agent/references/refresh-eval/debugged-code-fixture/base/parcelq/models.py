from dataclasses import dataclass
from typing import Optional


@dataclass
class Parcel:
    tracking_id: str
    weight_kg: float
    country: str
    recipient: str
    phone: Optional[str] = None
    company: Optional[str] = None
