from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TagSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    type: str | None
    created_at: datetime


class TagCreateSchema(BaseModel):
    name: str
    slug: str
    type: str | None = None


class TagUpdateSchema(BaseModel):
    name: str
    slug: str
    type: str | None = None
