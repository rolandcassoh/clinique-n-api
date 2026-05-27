from dataclasses import dataclass
from typing import Literal


@dataclass
class Language:
    id: int
    name: str
    code: str
    native_name: str | None
    flag: str | None
    is_default: bool
    is_active: bool
    direction: Literal["ltr", "rtl"]
