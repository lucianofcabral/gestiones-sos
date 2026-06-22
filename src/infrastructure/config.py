"""Application settings — single source of truth for all configuration."""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    """Centralized application configuration.

    All env var reads happen here, not scattered across adapters.
    Extend this class as new configuration needs arise.
    """

    storage_path: str = field(
        default_factory=lambda: os.environ.get(
            "DOCUMENTS_STORAGE_PATH", "./storage/documents"
        )
    )

    database_url: str = field(
        default_factory=lambda: os.environ.get("DATABASE_URL", "")
    )

    jwt_secret: str = field(
        default_factory=lambda: os.environ.get("JWT_SECRET", "")
    )
