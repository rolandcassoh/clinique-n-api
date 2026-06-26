"""Schemas Pydantic v2 du module slider."""
from pydantic import BaseModel, ConfigDict


class SliderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titre: str
    sous_titre: str | None
    image: str
    lien: str | None
    texte_bouton: str | None
    position: int


class SliderCreateSchema(BaseModel):
    titre: str
    sous_titre: str | None = None
    image: str
    lien: str | None = None
    texte_bouton: str | None = None
    position: int = 0
    est_actif: bool = True


class SliderUpdateSchema(BaseModel):
    titre: str
    sous_titre: str | None = None
    image: str
    lien: str | None = None
    texte_bouton: str | None = None
    position: int = 0
    est_actif: bool = True


class SliderReorderSchema(BaseModel):
    position: int
