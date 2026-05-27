from typing import Literal

from pydantic import BaseModel, ConfigDict


class LanguageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    native_name: str | None
    flag: str | None
    is_default: bool
    direction: Literal["ltr", "rtl"]


class LanguageCreateSchema(BaseModel):
    name: str
    code: str
    native_name: str | None = None
    flag: str | None = None
    is_default: bool = False
    is_active: bool = True
    direction: Literal["ltr", "rtl"] = "ltr"


class LanguageUpdateSchema(BaseModel):
    name: str
    code: str
    native_name: str | None = None
    flag: str | None = None
    is_default: bool = False
    is_active: bool = True
    direction: Literal["ltr", "rtl"] = "ltr"
