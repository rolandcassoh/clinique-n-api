from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class SettingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    value: Any
    type: Literal["text", "number", "boolean", "json"]
    group: str | None
    is_public: bool

    @classmethod
    def from_entity(cls, s) -> "SettingSchema":
        return cls(
            id=s.id, key=s.key, value=s.value,
            type=s.type, group=s.group, is_public=s.is_public,
        )


class SettingUpdateSchema(BaseModel):
    value: str | None = None
