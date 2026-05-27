from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class TagModel(BaseModel):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    type: Mapped[str | None] = mapped_column(String(50), nullable=True)
