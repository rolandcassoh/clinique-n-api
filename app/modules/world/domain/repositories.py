"""Interfaces (ABC) des repositories world."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.world.domain.entities import City, Country, State
from app.shared.schemas.pagination import PaginationParams


class CountryRepository(ABC):
    @abstractmethod
    async def list(
        self, params: PaginationParams, search: str | None = None
    ) -> tuple[list[Country], int]:
        """Retourne (pays, total) avec filtre optionnel sur name."""

    @abstractmethod
    async def get_by_id(self, country_id: int) -> Country | None:
        """Retourne un pays par son id ou None."""

    @abstractmethod
    async def list_states(self, country_id: int) -> list[State]:
        """Retourne les états d'un pays (non supprimés)."""


class StateRepository(ABC):
    @abstractmethod
    async def get_by_id(self, state_id: int) -> State | None:
        """Retourne un état par son id ou None."""

    @abstractmethod
    async def list_cities(self, state_id: int) -> list[City]:
        """Retourne les villes d'un état (non supprimées)."""


class CityRepository(ABC):
    @abstractmethod
    async def list(
        self,
        params: PaginationParams,
        state_id: int | None = None,
        search: str | None = None,
    ) -> tuple[list[City], int]:
        """Retourne (villes, total) avec filtres optionnels."""
