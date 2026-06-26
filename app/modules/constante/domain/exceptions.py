"""Exceptions métier du module constant (paramètres système)."""
from app.shared.exceptions.domain import EntityNotFoundError


class SettingNotFoundError(EntityNotFoundError):
    def __init__(self, cle: str) -> None:
        super().__init__("Setting", cle)
