from abc import ABC, abstractmethod
from datetime import date

from app.modules.customer.domain.entities import CustomerProfile, FamilyMember


class AbstractCustomerProfileRepository(ABC):
    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> CustomerProfile | None:
        ...

    @abstractmethod
    async def update(
        self,
        user_id: int,
        avatar: str | None = None,
        address: str | None = None,
        city_id: int | None = None,
        date_of_birth: date | None = None,
        gender: str | None = None,
        blood_group: str | None = None,
        bio: str | None = None,
    ) -> CustomerProfile | None:
        ...


class AbstractFamilyMemberRepository(ABC):
    @abstractmethod
    async def list_by_user(self, user_id: int) -> list[FamilyMember]:
        ...

    @abstractmethod
    async def get_by_id(self, member_id: int) -> FamilyMember | None:
        ...

    @abstractmethod
    async def create(
        self,
        user_id: int,
        name: str,
        relation: str,
        date_of_birth: date | None,
        gender: str | None,
        blood_group: str | None,
        phone: str | None,
    ) -> FamilyMember:
        ...

    @abstractmethod
    async def update(
        self,
        member_id: int,
        name: str,
        relation: str,
        date_of_birth: date | None,
        gender: str | None,
        blood_group: str | None,
        phone: str | None,
    ) -> FamilyMember | None:
        ...

    @abstractmethod
    async def soft_delete(self, member_id: int) -> bool:
        ...
