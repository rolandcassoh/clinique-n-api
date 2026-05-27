from abc import ABC, abstractmethod

from app.modules.auth.domain.entities import User


class UserRepositoryPort(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        pass

    @abstractmethod
    async def create(
        self,
        name: str,
        email: str,
        password_hash: str,
        username: str | None = None,
        phone: str | None = None,
    ) -> User:
        pass

    @abstractmethod
    async def update_otp(self, user_id: int, otp_code: str | None) -> None:
        pass

    @abstractmethod
    async def verify_email(self, user_id: int) -> None:
        pass

    @abstractmethod
    async def update_totp(self, user_id: int, secret: str | None, enabled: bool) -> None:
        pass

    @abstractmethod
    async def update_password(self, user_id: int, password_hash: str) -> None:
        pass

    @abstractmethod
    async def assign_role(self, user_id: int, role_name: str) -> None:
        pass
