"""StoragePort — abstraction for document storage backends."""

from typing import Protocol


class StoragePort(Protocol):
    """Port for content-addressable document storage.

    Implementations can be filesystem, S3, GCS, or in-memory for tests.
    """

    def save(self, content: bytes, ext: str) -> str:
        """Persist content and return its content-addressable hash.

        If content already exists, it's a no-op (dedup by hash).
        """
        ...

    def get(self, hash: str, ext: str) -> bytes:
        """Retrieve content by its hash and extension. Raises FileNotFoundError if missing."""
        ...

    def delete(self, hash: str, ext: str) -> None:
        """Remove stored content. No-op if hash doesn't exist."""
        ...

    def exists(self, hash: str, ext: str) -> bool:
        """Check if content with given hash exists."""
        ...
