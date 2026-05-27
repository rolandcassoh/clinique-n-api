from dataclasses import dataclass
from datetime import datetime


@dataclass
class Tag:
    id: int
    name: str
    slug: str
    type: str | None
    created_at: datetime
