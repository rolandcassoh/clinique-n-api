import base64
import io

import pyotp
import qrcode  # type: ignore[import]


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_totp_uri(secret: str, courriel: str, issuer: str = "Gestion Clinique") -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(nom=courriel, issuer_name=issuer)


def verify_totp_token(secret: str, jeton: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(jeton, valid_window=1)


def generate_totp_qr_base64(secret: str, courriel: str, issuer: str = "Gestion Clinique") -> str:
    uri = get_totp_uri(secret, courriel, issuer)
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode()
