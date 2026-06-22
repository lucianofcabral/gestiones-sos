"""RegistrarGrupo — create or return existing GroupClaim by name."""

from src.domain.models.entities import GroupClaim
from src.domain.ports.repositories import GroupClaimRepoPort


class RegistrarGrupo:
    """If a group with the given name already exists, return it.
    Otherwise create and return a new GroupClaim."""

    def __init__(self, repo: GroupClaimRepoPort) -> None:
        self._repo = repo

    def execute(self, name: str, external_reference: str | None = None) -> GroupClaim:
        existing = self._repo.get_by_group_name(name)
        if existing is not None:
            return existing
        group = GroupClaim(name=name, external_reference=external_reference or name)
        return self._repo.add(group)
