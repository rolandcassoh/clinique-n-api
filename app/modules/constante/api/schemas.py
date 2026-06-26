from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class SettingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cle: str
    valeur: Any
    type: Literal["text", "number", "boolean", "json"]
    groupe: str | None
    est_public: bool

    @classmethod
    def from_entity(cls, s) -> "SettingSchema":
        return cls(
            id=s.id, cle=s.cle, valeur=s.valeur,
            type=s.type, groupe=s.groupe, est_public=s.est_public,
        )


class SettingUpdateSchema(BaseModel):
    valeur: str | None = None
