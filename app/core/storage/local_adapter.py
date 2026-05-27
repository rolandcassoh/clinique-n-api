import os
from pathlib import Path

from app.core.storage.port import StoragePort

_STORAGE_ROOT = Path("storage/uploads")


class LocalStorageAdapter(StoragePort):
    def __init__(self, root: Path = _STORAGE_ROOT, base_url: str = "http://localhost:8000") -> None:
        self._root = root
        self._base_url = base_url.rstrip("/")
        self._root.mkdir(parents=True, exist_ok=True)

    async def save(self, path: str, content: bytes, content_type: str = "application/octet-stream") -> str:
        full_path = self._root / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return await self.get_url(path)

    async def delete(self, path: str) -> None:
        full_path = self._root / path
        if full_path.exists():
            os.remove(full_path)

    async def get_url(self, path: str) -> str:
        return f"{self._base_url}/storage/{path}"

    async def exists(self, path: str) -> bool:
        return (self._root / path).exists()
