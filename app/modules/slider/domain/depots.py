"""Interface (ABC) du repository slider."""
from abc import ABC, abstractmethod

from app.modules.slider.domain.entites import Slider


class AbstractSliderRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[Slider]:
        """Retourne toutes les bannières actives triées par position."""
        ...

    @abstractmethod
    async def get_by_id(self, slider_id: int) -> Slider | None:
        """Retourne une bannière par son id ou None."""
        ...

    @abstractmethod
    async def create(
        self, titre: str, sous_titre: str | None, image: str, lien: str | None,
        texte_bouton: str | None, position: int, est_actif: bool
    ) -> Slider:
        """Crée et retourne une nouvelle bannière."""
        ...

    @abstractmethod
    async def update(
        self, slider_id: int, titre: str, sous_titre: str | None, image: str,
        lien: str | None, texte_bouton: str | None, position: int, est_actif: bool
    ) -> Slider | None:
        """Met à jour une bannière, retourne None si inexistante."""
        ...

    @abstractmethod
    async def reorder(self, slider_id: int, position: int) -> Slider | None:
        """Modifie la position d'une bannière, retourne None si inexistante."""
        ...

    @abstractmethod
    async def soft_delete(self, slider_id: int) -> bool:
        """Suppression logique. Retourne True si trouvée, False sinon."""
        ...
