import json
from dataclasses import dataclass
from typing import Any, Literal


SettingType = Literal["text", "number", "boolean", "json"]


@dataclass
class Setting:
    id: int
    key: str
    raw_value: str | None
    type: SettingType
    group: str | None
    is_public: bool

    @property
    def value(self) -> Any:
        if self.raw_value is None:
            return None
        if self.type == "boolean":
            return self.raw_value.lower() in ("1", "true", "yes")
        if self.type == "number":
            return float(self.raw_value)
        if self.type == "json":
            return json.loads(self.raw_value)
        return self.raw_value
