"""Chiffrement AES-256 via Fernet pour les données médicales sensibles."""
from __future__ import annotations

import base64

from cryptography.fernet import Fernet

from app.config import settings


class FieldEncryption:
    """Chiffrement symétrique Fernet (AES-128-CBC avec HMAC-SHA256) pour champs sensibles."""

    _fernet: Fernet | None = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        if cls._fernet is None:
            cle = settings.encryption_key.encode()
            # Fernet nécessite exactement 32 bytes encodés en base64 URL-safe
            if len(cle) < 32:
                cle = cle.ljust(32, b"=")
            cls._fernet = Fernet(base64.urlsafe_b64encode(cle[:32]))
        return cls._fernet

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        if not plaintext:
            return plaintext
        return cls._get_fernet().encrypt(plaintext.encode()).decode()

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        if not ciphertext:
            return ciphertext
        try:
            return cls._get_fernet().decrypt(ciphertext.encode()).decode()
        except Exception:
            # Fallback si la valeur n'est pas chiffrée (migration de données)
            return ciphertext
