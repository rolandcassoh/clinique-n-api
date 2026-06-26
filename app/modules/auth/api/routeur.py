from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status as statut
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
from app.modules.auth.application.cas_utilisation import (
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
from app.modules.auth.infrastructure.depots import SQLAlchemyUserRepository

router = APIRouter(prefix="/api/auth", tags=["auth"])

_DOMAIN_ERROR_MAP: dict[type[Exception], int] = {
    InvalidCredentialsError: statut.HTTP_401_UNAUTHORIZED,
    AccountInactiveError: statut.HTTP_403_FORBIDDEN,
    EmailNotVerifiedError: statut.HTTP_403_FORBIDDEN,
    UserAlreadyExistsError: statut.HTTP_409_CONFLICT,
    UserNotFoundError: statut.HTTP_404_NOT_FOUND,
    InvalidOtpError: statut.HTTP_422_UNPROCESSABLE_ENTITY,
    InvalidTotpError: statut.HTTP_422_UNPROCESSABLE_ENTITY,
    TotpAlreadyEnabledError: statut.HTTP_409_CONFLICT,
    InvalidResetTokenError: statut.HTTP_422_UNPROCESSABLE_ENTITY,
}


def _handle_domain_error(exc: Exception) -> HTTPException:
    code = _DOMAIN_ERROR_MAP.get(type(exc), statut.HTTP_400_BAD_REQUEST)
    msg = getattr(exc, "message", str(exc))
    return HTTPException(status_code=code, detail=msg)


@router.post("/inscription", response_model=UserResponse, status_code=statut.HTTP_201_CREATED)
async def register(
    payload: RegisterSchema,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = RegisterUseCase(repo)
    try:
        utilisateur = await use_case.execute(
            RegisterCommand(
                nom=payload.nom,
                courriel=payload.courriel,
                mot_de_passe=payload.mot_de_passe,
                nom_utilisateur=payload.nom_utilisateur,
                telephone=payload.telephone,
            )
        )
    except Exception as exc:
        raise _handle_domain_error(exc) from exc

    return UserResponse(
        id=utilisateur.id,
        nom=utilisateur.nom,
        courriel=utilisateur.courriel,
        nom_utilisateur=utilisateur.nom_utilisateur,
        telephone=utilisateur.telephone,
        est_actif=utilisateur.est_actif,
        courriel_verifie_le=utilisateur.courriel_verifie_le,
        totp_actif=utilisateur.totp_actif,
        roles=utilisateur.roles,
        created_at=utilisateur.created_at,
    )


@router.post("/connexion", response_model=TokenResponseSchema)
async def login(
    payload: LoginSchema,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = LoginUseCase(repo)
    try:
        resultat = await use_case.execute(LoginCommand(courriel=payload.courriel, mot_de_passe=payload.mot_de_passe))
    except Exception as exc:
        raise _handle_domain_error(exc) from exc

    utilisateur = resultat["user"]
    return TokenResponseSchema(
        access_token=resultat["access_token"],
        refresh_token=resultat["refresh_token"],
        type_jeton=resultat["type_jeton"],
        user=UserResponse(
            id=utilisateur.id,
            nom=utilisateur.nom,
            courriel=utilisateur.courriel,
            nom_utilisateur=utilisateur.nom_utilisateur,
            telephone=utilisateur.telephone,
            est_actif=utilisateur.est_actif,
            courriel_verifie_le=utilisateur.courriel_verifie_le,
            totp_actif=utilisateur.totp_actif,
            roles=utilisateur.roles,
            created_at=utilisateur.created_at,
        ),
    )


@router.post("/jeton/rafraichir", response_model=AccessTokenResponseSchema)
async def refresh_token(
    payload: RefreshTokenSchema,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = RefreshTokenUseCase(repo)
    try:
        resultat = await use_case.execute(RefreshTokenCommand(refresh_token=payload.refresh_token))
    except Exception as exc:
        raise _handle_domain_error(exc) from exc

    return AccessTokenResponseSchema(
        access_token=resultat["access_token"],
        refresh_token=resultat["refresh_token"],
        type_jeton=resultat["type_jeton"],
    )


@router.delete("/deconnexion", response_model=MessageResponse)
async def logout(
    current_user: dict[str, Any] = Depends(get_current_user),
    redis: Any = Depends(get_redis),
) -> Any:
    jeton = current_user["jeton"]
    charge_utile = current_user["payload"]
    hachage_jeton = JWTHandler.hash_token(jeton)
    duree_restante = JWTHandler.remaining_ttl_seconds(charge_utile)

    if duree_restante > 0:
        await redis.setex(f"jeton:blacklist:{hachage_jeton}", duree_restante, "1")

    return MessageResponse(message="Déconnexion réussie.")


@router.post("/mot-de-passe-oublie", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordSchema,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = ForgotPasswordUseCase(repo)
    await use_case.execute(ForgotPasswordCommand(courriel=payload.courriel))
    return MessageResponse(message="Si l'courriel existe, un code de réinitialisation a été envoyé.")


@router.post("/reinitialiser-mot-de-passe", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordSchema,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = ResetPasswordUseCase(repo)
    try:
        await use_case.execute(
            ResetPasswordCommand(jeton=payload.jeton, new_password=payload.new_password),
            id_utilisateur=payload.id_utilisateur,
        )
    except Exception as exc:
        raise _handle_domain_error(exc) from exc

    return MessageResponse(message="Le mot de passe a été réinitialisé avec succès.")


@router.post("/double-auth/configuration", response_model=TotpSetupResponse)
async def setup_2fa(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = SetupTotpUseCase(repo)
    try:
        resultat = await use_case.execute(SetupTotpCommand(id_utilisateur=current_user["id"]))
    except Exception as exc:
        raise _handle_domain_error(exc) from exc

    return TotpSetupResponse(secret=resultat["secret"], qr_code=resultat["qr_code"])


@router.post("/double-auth/verifier", response_model=MessageResponse)
async def verify_2fa(
    payload: VerifyTotpSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = VerifyTotpUseCase(repo)
    try:
        await use_case.execute(VerifyTotpCommand(id_utilisateur=current_user["id"], jeton=payload.jeton))
    except Exception as exc:
        raise _handle_domain_error(exc) from exc

    return MessageResponse(message="Authentification à deux facteurs vérifiée et activée.")


@router.post("/otp/renvoyer", response_model=MessageResponse)
async def resend_otp(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    import random
    import string

    repo = SQLAlchemyUserRepository(db)
    code_otp = "".join(random.choices(string.digits, k=6))
    await repo.update_otp(current_user["id"], code_otp)
    # L'envoi de la notification est géré par l'adaptateur de notification
    return MessageResponse(message="Le code OTP a été renvoyé.")


@router.post("/otp/verifier", response_model=UserResponse)
async def verify_otp(
    payload: VerifyOtpSchema,
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    use_case = VerifyOtpUseCase(repo)
    try:
        utilisateur = await use_case.execute(VerifyOtpCommand(id_utilisateur=payload.id_utilisateur, code_otp=payload.code_otp))
    except Exception as exc:
        raise _handle_domain_error(exc) from exc

    return UserResponse(
        id=utilisateur.id,
        nom=utilisateur.nom,
        courriel=utilisateur.courriel,
        nom_utilisateur=utilisateur.nom_utilisateur,
        telephone=utilisateur.telephone,
        est_actif=utilisateur.est_actif,
        courriel_verifie_le=utilisateur.courriel_verifie_le,
        totp_actif=utilisateur.totp_actif,
        roles=utilisateur.roles,
        created_at=utilisateur.created_at,
    )


@router.get("/moi", response_model=UserResponse)
async def me(
    current_user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    repo = SQLAlchemyUserRepository(db)
    utilisateur = await repo.get_by_id(current_user["id"])
    if utilisateur is None:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    return UserResponse(
        id=utilisateur.id,
        nom=utilisateur.nom,
        courriel=utilisateur.courriel,
        nom_utilisateur=utilisateur.nom_utilisateur,
        telephone=utilisateur.telephone,
        est_actif=utilisateur.est_actif,
        courriel_verifie_le=utilisateur.courriel_verifie_le,
        totp_actif=utilisateur.totp_actif,
        roles=utilisateur.roles,
        created_at=utilisateur.created_at,
    )
