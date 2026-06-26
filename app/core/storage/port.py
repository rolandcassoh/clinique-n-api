from abc import ABC, abstractmethod


class StoragePort(ABC):
    @abstractmethod
    async def save(self, path: str, contenu: bytes, content_type: str = "application/octet-stream") -> str:
        """Persist contenu at path and return the public URL."""

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Remove the file at path."""

    @abstractmethod
    async def get_url(self, path: str) -> str:
        """Return the public URL for a stored file."""

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Return True if the file exists."""
