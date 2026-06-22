"""ObtenerGrupos — list all groups or search by text."""

from src.domain.models.entities import GroupClaim
from src.domain.ports.repositories import GroupClaimRepoPort


class ObtenerGrupos:
    """Return all GroupClaims (ordered by name) or search by text ILIKE."""

    def __init__(self, repo: GroupClaimRepoPort) -> None:
        self._repo = repo

    def execute(self) -> list[GroupClaim]:
        return self._repo.get_all()

    def buscar_por_texto(self, text: str) -> list[GroupClaim]:
        return self._repo.get_by_text_like(text)
