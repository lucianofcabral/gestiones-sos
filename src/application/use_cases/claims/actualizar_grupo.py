"""ActualizarGrupo — update a GroupClaim name by group_id."""

from uuid import UUID

from src.domain.models.entities import GroupClaim
from src.domain.ports.repositories import GroupClaimRepoPort


class ActualizarGrupo:
    """Update the name of a GroupClaim.

    Returns the updated GroupClaim on success, None if not found.
    Raises ValueError if the new name conflicts with an existing group.
    """

    def __init__(self, repo: GroupClaimRepoPort) -> None:
        self._repo = repo

    def execute(self, group_id: UUID, name: str) -> GroupClaim | None:
        existing = self._repo.get_by_id(group_id)
        if existing is None:
            return None

        # Check for duplicate name (excluding self)
        existing_with_name = self._repo.get_by_group_name(name)
        if existing_with_name is not None and existing_with_name.group_id != group_id:
            raise ValueError(f"Ya existe un grupo con el nombre '{name}'")

        updated = GroupClaim(
            group_id=group_id, name=name, created_at=existing.created_at
        )
        if self._repo.update(group_id, updated):
            return updated
        return None
