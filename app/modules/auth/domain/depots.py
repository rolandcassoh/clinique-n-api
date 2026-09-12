from abc import ABC, abstractmethod

from app.modules.auth.domain.entites import User


class UserRepositoryPort(ABC):
    @abstractmethod
    async def get_by_id(self, id_utilisateur: int) -> User | None:
        pass

    @abstractmethod
    async def get_by_email(self, courriel: str) -> User | None:
        pass

    @abstractmethod
    async def get_by_username(self, nom_utilisateur: str) -> User | None:
        pass

    @abstractmethod
    async def create(
        self,
        nom: str,
        courriel: str,
        password_hash: str,
        nom_utilisateur: str | None = None,
        telephone: str | None = None,
    ) -> User:
        pass

    @abstractmethod
    async def update_otp(self, id_utilisateur: int, code_otp: str | None) -> None:
        pass

    @abstractmethod
    async def verify_email(self, id_utilisateur: int) -> None:
        pass

    @abstractmethod
    async def update_totp(self, id_utilisateur: int, secret: str | None, enabled: bool) -> None:
        pass

    @abstractmethod
    async def update_password(self, id_utilisateur: int, password_hash: str) -> None:
        pass

    @abstractmethod
    async def update_profile(
        self,
        id_utilisateur: int,
        nom: str | None = None,
        telephone: str | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def assign_role(self, id_utilisateur: int, role_name: str) -> None:
        pass
