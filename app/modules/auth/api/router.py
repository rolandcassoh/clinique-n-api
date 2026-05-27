from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user
from app.core.auth.jwt_handler import JWTHandler
from app.core.cache.redis_client import get_redis
from app.database import get_db
from app.modules.auth.api.schemas import (
    AccessTokenResponseSchema,
    ForgotPasswordSchema,
    LoginSchema,
    MessageResponse,
    RefreshTokenSchema,
    RegisterSchema,
    ResetPasswordSchema,
    TokenResponseSchema,
    TotpSetupResponse,
    UserResponse,
    VerifyOtpSchema,
    VerifyTotpSchema,
)
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
from app.modules.auth.application.use_cases import (
    ForgotPasswordUseCase,
    LoginUseCase,
    RefreshTokenUseCase,
    RegisterUseCase,
    ResetPasswordUseCase,
    SetupTotpUseCase,
    VerifyOtpUseCase,
    VerifyTotpUseCase,
)
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
from app.modules.auth.infrastructure.repositories import SQLAlchemyUserRepository

router = APIRouter(prefix="/api/auth", tags=["auth"])

_DOMAIN_ERROR_MAP: dict[type[Exception], int] = {
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    AccountInactiveError: status.HTTP_403_FORBIDDEN,
    EmailNotVerifiedError: status.HTTP_403_FORBIDDEN,
    UserAlreadyExistsError: status.HTTP_409_CONFLICT,
    UserNotFoundError: status.HTTP_404_NOT_FOUND,
    InvalidOtpError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    InvalidTotpError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    TotpAlreadyEnabledError: status.HTTP_409_CONFLICT,
    InvalidResetTokenError: status.HTTP_422_UNPROCESSABLE_ENTITY,
}


def _handle_domain_error(exc: Exception) -> HTTPException:
    code = _DOMAIN_ERROR_MAP.get(type(exc), status.HTTP_400_BAD_REQUEST)
    msg = getattr(exc, "message", str(exc))
    return HTTPException(status_code=code, detail=msg)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterSchema,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = RegisterUseCase(repo)
    try:
        user = await use_case.execute(
            RegisterCommand(
                name=payload.name,
                email=payload.email,
                password=payload.password,
                username=payload.username,
                phone=payload.phone,
            )
        )
    except Exception as exc:
        raise _handle_domain_error(exc) from exc

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        username=user.username,
        phone=user.phone,
        is_active=user.is_active,
        email_verified_at=user.email_verified_at,
        totp_enabled=user.totp_enabled,
        roles=user.roles,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponseSchema)
async def login(
    payload: LoginSchema,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = LoginUseCase(repo)
    try:
        result = await use_case.execute(LoginCommand(email=payload.email, password=payload.password))
    except Exception as exc:
        raise _handle_domain_error(exc) from exc

    user = result["user"]
    return TokenResponseSchema(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            username=user.username,
            phone=user.phone,
            is_active=user.is_active,
            email_verified_at=user.email_verified_at,
            totp_enabled=user.totp_enabled,
            roles=user.roles,
            created_at=user.created_at,
        ),
    )


@router.post("/token/refresh", response_model=AccessTokenResponseSchema)
async def refresh_token(
    payload: RefreshTokenSchema,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = RefreshTokenUseCase(repo)
    try:
        result = await use_case.execute(RefreshTokenCommand(refresh_token=payload.refresh_token))
    except Exception as exc:
        raise _handle_domain_error(exc) from exc

    return AccessTokenResponseSchema(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
    )


@router.delete("/logout", response_model=MessageResponse)
async def logout(
    current_user: dict[str, Any] = Depends(get_current_user),
    redis: Any = Depends(get_redis),
) -> Any:
    token = current_user["token"]
    payload = current_user["payload"]
    token_hash = JWTHandler.hash_token(token)
    ttl = JWTHandler.remaining_ttl_seconds(payload)

    if ttl > 0:
        await redis.setex(f"token:blacklist:{token_hash}", ttl, "1")

    return MessageResponse(message="Successfully logged out.")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordSchema,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = ForgotPasswordUseCase(repo)
    await use_case.execute(ForgotPasswordCommand(email=payload.email))
    return MessageResponse(message="If the email exists, a reset code has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordSchema,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = ResetPasswordUseCase(repo)
    try:
        await use_case.execute(
            ResetPasswordCommand(token=payload.token, new_password=payload.new_password),
            user_id=payload.user_id,
        )
    except Exception as exc:
        raise _handle_domain_error(exc) from exc

    return MessageResponse(message="Password has been reset successfully.")


@router.post("/2fa/setup", response_model=TotpSetupResponse)
async def setup_2fa(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = SetupTotpUseCase(repo)
    try:
        result = await use_case.execute(SetupTotpCommand(user_id=current_user["id"]))
    except Exception as exc:
        raise _handle_domain_error(exc) from exc

    return TotpSetupResponse(secret=result["secret"], qr_code=result["qr_code"])


@router.post("/2fa/verify", response_model=MessageResponse)
async def verify_2fa(
    payload: VerifyTotpSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = VerifyTotpUseCase(repo)
    try:
        await use_case.execute(VerifyTotpCommand(user_id=current_user["id"], token=payload.token))
    except Exception as exc:
        raise _handle_domain_error(exc) from exc

    return MessageResponse(message="Two-factor authentication verified and enabled.")


@router.post("/otp/resend", response_model=MessageResponse)
async def resend_otp(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    import random
    import string

    repo = SQLAlchemyUserRepository(db)
    otp = "".join(random.choices(string.digits, k=6))
    await repo.update_otp(current_user["id"], otp)
    # Notification delivery happens via the notification adapter
    return MessageResponse(message="OTP code has been resent.")


@router.post("/otp/verify", response_model=UserResponse)
async def verify_otp(
    payload: VerifyOtpSchema,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = VerifyOtpUseCase(repo)
    try:
        user = await use_case.execute(VerifyOtpCommand(user_id=payload.user_id, otp_code=payload.otp_code))
    except Exception as exc:
        raise _handle_domain_error(exc) from exc

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        username=user.username,
        phone=user.phone,
        is_active=user.is_active,
        email_verified_at=user.email_verified_at,
        totp_enabled=user.totp_enabled,
        roles=user.roles,
        created_at=user.created_at,
    )


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    user = await repo.get_by_id(current_user["id"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        username=user.username,
        phone=user.phone,
        is_active=user.is_active,
        email_verified_at=user.email_verified_at,
        totp_enabled=user.totp_enabled,
        roles=user.roles,
        created_at=user.created_at,
    )
