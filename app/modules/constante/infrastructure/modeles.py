from sqlalchemy import Boolean, Enum, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.shared.models.base import Base


class SettingModel(Base):
    """Settings table — pas de soft delete, pas d'héritage de BaseModel."""

    __tablename__ = "parametres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cle: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    valeur: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(
        Enum("text", "number", "boolean", "json", name="setting_type"),
        nullable=False,
        default="text",
    )
    groupe: Mapped[str | None] = mapped_column(String(100), nullable=True)
    est_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
