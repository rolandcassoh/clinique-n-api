"""Interface (ABC) du repository langue (language)."""
from abc import ABC, abstractmethod
from typing import Literal

from app.modules.langue.domain.entites import Language


class AbstractLanguageRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[Language]:
        """Retourne toutes les langues actives."""
        ...

    @abstractmethod
    async def get_default(self) -> Language | None:
        """Retourne la langue par défaut ou None."""
        ...

    @abstractmethod
    async def get_by_id(self, language_id: int) -> Language | None:
        """Retourne une langue par son id ou None."""
        ...

    @abstractmethod
    async def get_by_code(self, code: str) -> Language | None:
        """Retourne une langue par son code ou None."""
        ...

    @abstractmethod
    async def create(
        self, nom: str, code: str, nom_natif: str | None, drapeau: str | None,
        est_defaut: bool, est_actif: bool, sens_ecriture: Literal["ltr", "rtl"]
    ) -> Language:
        """Crée et retourne une nouvelle langue."""
        ...

    @abstractmethod
    async def update(
        self, language_id: int, nom: str, code: str, nom_natif: str | None,
        drapeau: str | None, est_defaut: bool, est_actif: bool, sens_ecriture: Literal["ltr", "rtl"]
    ) -> Language | None:
        """Met à jour une langue, retourne None si inexistante."""
        ...

    @abstractmethod
    async def set_default(self, language_id: int) -> Language | None:
        """Définit cette langue comme langue par défaut (réinitialise les autres)."""
        ...
