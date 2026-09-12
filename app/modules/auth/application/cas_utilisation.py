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
from app.modules.auth.domain.entites import User
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
from app.modules.auth.domain.depots import UserRepositoryPort


def _generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


class RegisterUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: RegisterCommand) -> User:
        existant = await self._repo.get_by_email(command.courriel)
        if existant:
            raise UserAlreadyExistsError(command.courriel)

        hachage = hash_password(command.mot_de_passe)
        utilisateur = await self._repo.create(
            nom=command.nom,
            courriel=command.courriel,
            password_hash=hachage,
            nom_utilisateur=command.nom_utilisateur,
            telephone=command.telephone,
        )

        code_otp = _generate_otp()
        await self._repo.update_otp(utilisateur.id, code_otp)
        # NOTE : l'envoi du code OTP est délégué à l'adaptateur de notification configuré dans le routeur
        return utilisateur


class LoginUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: LoginCommand) -> dict[str, Any]:
        utilisateur = await self._repo.get_by_email(command.courriel)
        if utilisateur is None:
            raise InvalidCredentialsError()

        if not verify_password(command.mot_de_passe, utilisateur.mot_de_passe):
            raise InvalidCredentialsError()

        if not utilisateur.est_actif:
            raise AccountInactiveError()

        jeton_acces = JWTHandler.create_access_token(utilisateur.id, utilisateur.roles)
        jeton_rafraichissement = JWTHandler.create_refresh_token(utilisateur.id)

        return {
            "access_token": jeton_acces,
            "refresh_token": jeton_rafraichissement,
            "type_jeton": "Bearer",
            "user": utilisateur,
        }


class RefreshTokenUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: RefreshTokenCommand) -> dict[str, Any]:
        from jose import JWTError

        try:
            charge_utile = JWTHandler.decode_refresh_token(command.refresh_token)
        except JWTError:
            raise InvalidCredentialsError()

        id_utilisateur = int(charge_utile["sub"])
        utilisateur = await self._repo.get_by_id(id_utilisateur)
        if utilisateur is None:
            raise UserNotFoundError(id_utilisateur)

        if not utilisateur.est_actif:
            raise AccountInactiveError()

        jeton_acces = JWTHandler.create_access_token(utilisateur.id, utilisateur.roles)
        nouveau_rafraichissement = JWTHandler.create_refresh_token(utilisateur.id)

        return {
            "access_token": jeton_acces,
            "refresh_token": nouveau_rafraichissement,
            "type_jeton": "Bearer",
        }


class VerifyOtpUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: VerifyOtpCommand) -> User:
        utilisateur = await self._repo.get_by_id(command.id_utilisateur)
        if utilisateur is None:
            raise UserNotFoundError(command.id_utilisateur)

        if utilisateur.code_otp != command.code_otp:
            raise InvalidOtpError()

        await self._repo.verify_email(utilisateur.id)
        await self._repo.update_otp(utilisateur.id, None)

        # Recharger l'utilisateur pour refléter l'état vérifié
        mis_a_jour = await self._repo.get_by_id(utilisateur.id)
        assert mis_a_jour is not None
        return mis_a_jour


class SetupTotpUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: SetupTotpCommand) -> dict[str, str]:
        utilisateur = await self._repo.get_by_id(command.id_utilisateur)
        if utilisateur is None:
            raise UserNotFoundError(command.id_utilisateur)

        if utilisateur.totp_actif:
            raise TotpAlreadyEnabledError()

        secret = generate_totp_secret()
        await self._repo.update_totp(utilisateur.id, secret, enabled=False)

        qr_base64 = generate_totp_qr_base64(secret, utilisateur.courriel)
        return {"secret": secret, "qr_code": qr_base64}


class VerifyTotpUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: VerifyTotpCommand) -> bool:
        utilisateur = await self._repo.get_by_id(command.id_utilisateur)
        if utilisateur is None:
            raise UserNotFoundError(command.id_utilisateur)

        if not utilisateur.secret_totp:
            raise InvalidTotpError()

        if not verify_totp_token(utilisateur.secret_totp, command.jeton):
            raise InvalidTotpError()

        if not utilisateur.totp_actif:
            await self._repo.update_totp(utilisateur.id, utilisateur.secret_totp, enabled=True)

        return True


class ForgotPasswordUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: ForgotPasswordCommand) -> str:
        utilisateur = await self._repo.get_by_email(command.courriel)
        # Ne pas révéler si l'courriel existe ou non
        if utilisateur is None:
            return ""

        code_otp = _generate_otp(8)
        await self._repo.update_otp(utilisateur.id, code_otp)
        # L'envoi du code OTP est délégué à l'adaptateur de notification
        return code_otp


class ResetPasswordUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(self, command: ResetPasswordCommand, id_utilisateur: int) -> None:
        utilisateur = await self._repo.get_by_id(id_utilisateur)
        if utilisateur is None:
            raise UserNotFoundError(id_utilisateur)

        if utilisateur.code_otp != command.jeton:
            raise InvalidResetTokenError()

        hachage = hash_password(command.new_password)
        await self._repo.update_password(utilisateur.id, hachage)


class UpdateProfileUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(
        self,
        id_utilisateur: int,
        nom: str | None = None,
        telephone: str | None = None,
    ) -> User:
        utilisateur = await self._repo.get_by_id(id_utilisateur)
        if utilisateur is None:
            raise UserNotFoundError(id_utilisateur)

        await self._repo.update_profile(id_utilisateur, nom=nom, telephone=telephone)
        return await self._repo.get_by_id(id_utilisateur)  # type: ignore[return-value]


class ChangePasswordUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._repo = user_repo

    async def execute(
        self, id_utilisateur: int, mot_de_passe_actuel: str, nouveau_mot_de_passe: str
    ) -> None:
        utilisateur = await self._repo.get_by_id(id_utilisateur)
        if utilisateur is None:
            raise UserNotFoundError(id_utilisateur)

        if not verify_password(mot_de_passe_actuel, utilisateur.mot_de_passe):
            raise InvalidCredentialsError()

        hachage = hash_password(nouveau_mot_de_passe)
        await self._repo.update_password(id_utilisateur, hachage)
        await self._repo.update_otp(utilisateur.id, None)
