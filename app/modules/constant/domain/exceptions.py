from app.shared.exceptions.domain import EntityNotFoundError


class SettingNotFoundError(EntityNotFoundError):
    def __init__(self, key: str) -> None:
        super().__init__("Setting", key)
