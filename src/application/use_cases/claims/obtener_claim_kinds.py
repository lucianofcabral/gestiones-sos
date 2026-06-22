"""ObtenerClaimKinds — list all claim kinds."""

from src.domain.models.entities import ClaimKind
from src.domain.ports.repositories import ClaimKindRepoPort


class ObtenerClaimKinds:
    """Return all ClaimKinds (ordered by name)."""

    def __init__(self, repo: ClaimKindRepoPort) -> None:
        self._repo = repo

    def execute(self) -> list[ClaimKind]:
        return self._repo.get_all()
