from typing import Literal

from pydantic import BaseModel, ConfigDict


class LanguageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    code: str
    nom_natif: str | None
    drapeau: str | None
    est_defaut: bool
    sens_ecriture: Literal["ltr", "rtl"]


class LanguageCreateSchema(BaseModel):
    nom: str
    code: str
    nom_natif: str | None = None
    drapeau: str | None = None
    est_defaut: bool = False
    est_actif: bool = True
    sens_ecriture: Literal["ltr", "rtl"] = "ltr"


class LanguageUpdateSchema(BaseModel):
    nom: str
    code: str
    nom_natif: str | None = None
    drapeau: str | None = None
    est_defaut: bool = False
    est_actif: bool = True
    sens_ecriture: Literal["ltr", "rtl"] = "ltr"
