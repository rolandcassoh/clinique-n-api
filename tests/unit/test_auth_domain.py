"""Unit tests for auth domain — pure Python, no I/O."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.core.auth.jwt_handler import JWTHandler
from app.core.auth.password import hash_password, verify_password
from app.modules.auth.application.commands import LoginCommand, RegisterCommand
from app.modules.auth.application.use_cases import LoginUseCase, RegisterUseCase
from app.modules.auth.domain.entities import User
from app.modules.auth.domain.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from app.modules.auth.domain.repositories import UserRepositoryPort


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(**kwargs: Any) -> User:
    defaults: dict[str, Any] = {
        "id": 1,
        "name": "Alice Dupont",
        "email": "alice@clinique.app",
        "password": hash_password("Secret123!"),
        "username": "alice",
        "phone": None,
        "is_active": True,
        "email_verified_at": datetime.utcnow(),
        "otp_code": None,
        "totp_secret": None,
        "totp_enabled": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "deleted_at": None,
        "roles": ["patient"],
        "profile": None,
    }
    defaults.update(kwargs)
    return User(**defaults)


class _InMemoryUserRepo(UserRepositoryPort):
    def __init__(self) -> None:
        self._users: dict[int, User] = {}
        self._next_id = 1

    async def get_by_id(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._users.values() if u.email == email), None)

    async def get_by_username(self, username: str) -> User | None:
        return next((u for u in self._users.values() if u.username == username), None)

    async def create(
        self,
        name: str,
        email: str,
        password_hash: str,
        username: str | None = None,
        phone: str | None = None,
    ) -> User:
        user = _make_user(
            id=self._next_id,
            name=name,
            email=email,
            password=password_hash,
            username=username,
            phone=phone,
            email_verified_at=None,
        )
        self._users[self._next_id] = user
        self._next_id += 1
        return user

    async def update_otp(self, user_id: int, otp_code: str | None) -> None:
        if user_id in self._users:
            u = self._users[user_id]
            self._users[user_id] = _make_user(**{**u.__dict__, "otp_code": otp_code})

    async def verify_email(self, user_id: int) -> None:
        if user_id in self._users:
            u = self._users[user_id]
            self._users[user_id] = _make_user(
                **{**u.__dict__, "email_verified_at": datetime.utcnow()}
            )

    async def update_totp(self, user_id: int, secret: str | None, enabled: bool) -> None:
        if user_id in self._users:
            u = self._users[user_id]
            self._users[user_id] = _make_user(
                **{**u.__dict__, "totp_secret": secret, "totp_enabled": enabled}
            )

    async def update_password(self, user_id: int, password_hash: str) -> None:
        if user_id in self._users:
            u = self._users[user_id]
            self._users[user_id] = _make_user(**{**u.__dict__, "password": password_hash})

    async def assign_role(self, user_id: int, role_name: str) -> None:
        if user_id in self._users:
            u = self._users[user_id]
            roles = list(u.roles) + [role_name]
            self._users[user_id] = _make_user(**{**u.__dict__, "roles": roles})


# ---------------------------------------------------------------------------
# Entity tests
# ---------------------------------------------------------------------------

class TestUserEntity:
    def test_has_role_returns_true_when_role_present(self) -> None:
        user = _make_user(roles=["admin", "doctor"])
        assert user.has_role("admin") is True

    def test_has_role_returns_false_when_absent(self) -> None:
        user = _make_user(roles=["patient"])
        assert user.has_role("admin") is False

    def test_has_any_role(self) -> None:
        user = _make_user(roles=["doctor"])
        assert user.has_any_role("admin", "doctor") is True
        assert user.has_any_role("admin", "super-admin") is False

    def test_is_email_verified_false_when_no_date(self) -> None:
        user = _make_user(email_verified_at=None)
        assert user.is_email_verified is False

    def test_is_email_verified_true_when_date_set(self) -> None:
        user = _make_user(email_verified_at=datetime.utcnow())
        assert user.is_email_verified is True

    def test_is_deleted_false_by_default(self) -> None:
        user = _make_user(deleted_at=None)
        assert user.is_deleted is False

    def test_is_deleted_true_when_deleted_at_set(self) -> None:
        user = _make_user(deleted_at=datetime.utcnow())
        assert user.is_deleted is True


# ---------------------------------------------------------------------------
# Password tests
# ---------------------------------------------------------------------------

class TestPassword:
    def test_hash_and_verify(self) -> None:
        plain = "MyP@ssw0rd!"
        hashed = hash_password(plain)
        assert hashed != plain
        assert verify_password(plain, hashed) is True

    def test_wrong_password_fails(self) -> None:
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False


# ---------------------------------------------------------------------------
# JWT tests
# ---------------------------------------------------------------------------

class TestJWTHandler:
    def test_access_token_round_trip(self) -> None:
        token = JWTHandler.create_access_token(user_id=42, roles=["admin"])
        payload = JWTHandler.decode_access_token(token)
        assert payload["sub"] == "42"
        assert payload["type"] == "access"
        assert "admin" in payload["roles"]

    def test_refresh_token_round_trip(self) -> None:
        token = JWTHandler.create_refresh_token(user_id=7)
        payload = JWTHandler.decode_refresh_token(token)
        assert payload["sub"] == "7"
        assert payload["type"] == "refresh"

    def test_access_token_rejected_as_refresh(self) -> None:
        from jose import JWTError

        token = JWTHandler.create_access_token(user_id=1, roles=[])
        with pytest.raises(JWTError):
            JWTHandler.decode_refresh_token(token)

    def test_token_hash_is_deterministic(self) -> None:
        t = "some.token.value"
        assert JWTHandler.hash_token(t) == JWTHandler.hash_token(t)

    def test_remaining_ttl_positive_for_fresh_token(self) -> None:
        token = JWTHandler.create_access_token(user_id=1, roles=[])
        payload = JWTHandler.decode_access_token(token)
        ttl = JWTHandler.remaining_ttl_seconds(payload)
        assert ttl > 0


# ---------------------------------------------------------------------------
# RegisterUseCase tests
# ---------------------------------------------------------------------------

class TestRegisterUseCase:
    @pytest.mark.asyncio
    async def test_register_creates_user(self) -> None:
        repo = _InMemoryUserRepo()
        uc = RegisterUseCase(repo)
        user = await uc.execute(
            RegisterCommand(
                name="Bob Martin",
                email="bob@clinique.app",
                password="Secure123!",
            )
        )
        assert user.id == 1
        assert user.email == "bob@clinique.app"

    @pytest.mark.asyncio
    async def test_register_raises_if_email_exists(self) -> None:
        repo = _InMemoryUserRepo()
        uc = RegisterUseCase(repo)
        cmd = RegisterCommand(name="Bob", email="bob@clinique.app", password="Secure123!")
        await uc.execute(cmd)

        with pytest.raises(UserAlreadyExistsError):
            await uc.execute(cmd)


# ---------------------------------------------------------------------------
# LoginUseCase tests
# ---------------------------------------------------------------------------

class TestLoginUseCase:
    @pytest.mark.asyncio
    async def test_login_returns_tokens(self) -> None:
        repo = _InMemoryUserRepo()
        await repo.create("Alice", "alice@clinique.app", hash_password("pass123"))

        uc = LoginUseCase(repo)
        result = await uc.execute(LoginCommand(email="alice@clinique.app", password="pass123"))

        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "Bearer"

    @pytest.mark.asyncio
    async def test_login_raises_on_wrong_password(self) -> None:
        repo = _InMemoryUserRepo()
        await repo.create("Alice", "alice@clinique.app", hash_password("pass123"))

        uc = LoginUseCase(repo)
        with pytest.raises(InvalidCredentialsError):
            await uc.execute(LoginCommand(email="alice@clinique.app", password="wrong"))

    @pytest.mark.asyncio
    async def test_login_raises_on_unknown_email(self) -> None:
        repo = _InMemoryUserRepo()
        uc = LoginUseCase(repo)
        with pytest.raises(InvalidCredentialsError):
            await uc.execute(LoginCommand(email="ghost@clinique.app", password="pass"))
