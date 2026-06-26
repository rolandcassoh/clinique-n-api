"""Interfaces (ABC) des repositories client (customer)."""
from abc import ABC, abstractmethod
from datetime import date

from app.modules.client.domain.entites import CustomerProfile, FamilyMember


class AbstractCustomerProfileRepository(ABC):
    @abstractmethod
    async def get_by_user_id(self, id_utilisateur: int) -> CustomerProfile | None:
        ...

    @abstractmethod
    async def update(
        self,
        id_utilisateur: int,
        avatar: str | None = None,
        adresse: str | None = None,
        id_ville: int | None = None,
        date_naissance: date | None = None,
        sexe: str | None = None,
        groupe_sanguin: str | None = None,
        biographie: str | None = None,
    ) -> CustomerProfile | None:
        ...


class AbstractFamilyMemberRepository(ABC):
    @abstractmethod
    async def list_by_user(self, id_utilisateur: int) -> list[FamilyMember]:
        ...

    @abstractmethod
    async def get_by_id(self, member_id: int) -> FamilyMember | None:
        ...

    @abstractmethod
    async def create(
        self,
        id_utilisateur: int,
        nom: str,
        relation: str,
        date_naissance: date | None,
        sexe: str | None,
        groupe_sanguin: str | None,
        telephone: str | None,
    ) -> FamilyMember:
        ...

    @abstractmethod
    async def update(
        self,
        member_id: int,
        nom: str,
        relation: str,
        date_naissance: date | None,
        sexe: str | None,
        groupe_sanguin: str | None,
        telephone: str | None,
    ) -> FamilyMember | None:
        ...

    @abstractmethod
    async def soft_delete(self, member_id: int) -> bool:
        ...
