import random
import string
from typing import Any

from app.core.auth.jwt_handler import JWTHandler
from app.core.auth.password import hash_password, verify_password
from app.core.auth.totp import generate_totp_secret, generate_totp_qr_base64, verify_totp_token
from app.modules.auth.application.commands import (
    ForgotPasswordCommand,
    LoginCommand,
    RefreshTokenCommand,
    RegisterCommand,
    ResetPasswordCommand,
    SetupTotpCommand,
    VerifyOtpCommand,
    VerifyTotpCommand,
)
from app.modules.auth.domain.entities import User
from app.modules.auth.domain.exceptions import (
    AccountInactiveError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidOtpError,
    InvalidResetTokenError,
    InvalidTotpError,
    TotpAlreadyEnabledError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.modules.auth.domain.repositories import UserRepositoryPort


def _generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


class RegisterUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: RegisterCommand) -> User:
        existing = await self._repo.get_by_email(command.email)
        if existing:
            raise UserAlreadyExistsError(command.email)

        hashed = hash_password(command.password)
        user = await self._repo.create(
            name=command.name,
            email=command.email,
            password_hash=hashed,
            username=command.username,
            phone=command.phone,
        )

        otp = _generate_otp()
        await self._repo.update_otp(user.id, otp)
        # NOTE: OTP delivery is handled by the notification adapter wired in the router
        return user


class LoginUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: LoginCommand) -> dict[str, Any]:
        user = await self._repo.get_by_email(command.email)
        if user is None:
            raise InvalidCredentialsError()

        if not verify_password(command.password, user.password):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AccountInactiveError()

        access_token = JWTHandler.create_access_token(user.id, user.roles)
        refresh_token = JWTHandler.create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "user": user,
        }


class RefreshTokenUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: RefreshTokenCommand) -> dict[str, Any]:
        from jose import JWTError

        try:
            payload = JWTHandler.decode_refresh_token(command.refresh_token)
        except JWTError:
            raise InvalidCredentialsError()

        user_id = int(payload["sub"])
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        if not user.is_active:
            raise AccountInactiveError()

        access_token = JWTHandler.create_access_token(user.id, user.roles)
        new_refresh = JWTHandler.create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": new_refresh,
            "token_type": "Bearer",
        }


class VerifyOtpUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: VerifyOtpCommand) -> User:
        user = await self._repo.get_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError(command.user_id)

        if user.otp_code != command.otp_code:
            raise InvalidOtpError()

        await self._repo.verify_email(user.id)
        await self._repo.update_otp(user.id, None)

        # Reload user to reflect verified state
        updated = await self._repo.get_by_id(user.id)
        assert updated is not None
        return updated


class SetupTotpUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: SetupTotpCommand) -> dict[str, str]:
        user = await self._repo.get_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError(command.user_id)

        if user.totp_enabled:
            raise TotpAlreadyEnabledError()

        secret = generate_totp_secret()
        await self._repo.update_totp(user.id, secret, enabled=False)

        qr_base64 = generate_totp_qr_base64(secret, user.email)
        return {"secret": secret, "qr_code": qr_base64}


class VerifyTotpUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: VerifyTotpCommand) -> bool:
        user = await self._repo.get_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError(command.user_id)

        if not user.totp_secret:
            raise InvalidTotpError()

        if not verify_totp_token(user.totp_secret, command.token):
            raise InvalidTotpError()

        if not user.totp_enabled:
            await self._repo.update_totp(user.id, user.totp_secret, enabled=True)

        return True


class ForgotPasswordUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: ForgotPasswordCommand) -> str:
        user = await self._repo.get_by_email(command.email)
        # Don't leak whether email exists
        if user is None:
            return ""

        otp = _generate_otp(8)
        await self._repo.update_otp(user.id, otp)
        # OTP delivery delegated to notification adapter
        return otp


class ResetPasswordUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: ResetPasswordCommand, user_id: int) -> None:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        if user.otp_code != command.token:
            raise InvalidResetTokenError()

        hashed = hash_password(command.new_password)
        await self._repo.update_password(user.id, hashed)
        await self._repo.update_otp(user.id, None)
