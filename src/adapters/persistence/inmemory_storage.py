"""In-memory implementation of StoragePort for tests."""

import hashlib


class InMemoryStorageService:
    """In-memory storage that mimics content-addressable storage for tests."""

    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    def save(self, content: bytes, ext: str) -> str:
        hash = hashlib.sha256(content).hexdigest()
        key = f"{hash}.{ext}"
        if key not in self._store:
            self._store[key] = content
        return hash

    def get(self, hash: str, ext: str) -> bytes:
        key = f"{hash}.{ext}"
        if key not in self._store:
            msg = f"[Errno 2] No such file: '{key}'"
            raise FileNotFoundError(msg)
        return self._store[key]

    def delete(self, hash: str, ext: str) -> None:
        key = f"{hash}.{ext}"
        self._store.pop(key, None)

    def exists(self, hash: str, ext: str) -> bool:
        key = f"{hash}.{ext}"
        return key in self._store
