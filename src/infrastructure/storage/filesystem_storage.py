"""Content-addressable filesystem storage using SHA-256 hash."""

import hashlib
import os
from pathlib import Path


class FilesystemStorageService:
    def __init__(self, base_path: str | None = None):
        self._base = Path(
            base_path or os.environ.get("DOCUMENTS_STORAGE_PATH", "./storage/documents")
        )

    def _path_from_hash(self, hash: str, ext: str) -> Path:
        return self._base / hash[:2] / hash[2:4] / f"{hash}.{ext}"

    def save(self, content: bytes, ext: str) -> str:
        hash = hashlib.sha256(content).hexdigest()
        dest = self._path_from_hash(hash, ext)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            dest.write_bytes(content)
        return hash

    def get(self, hash: str, ext: str) -> bytes:
        return self._path_from_hash(hash, ext).read_bytes()

    def delete(self, hash: str, ext: str) -> None:
        path = self._path_from_hash(hash, ext)
        if path.exists():
            path.unlink()

    def exists(self, hash: str, ext: str) -> bool:
        return self._path_from_hash(hash, ext).exists()
