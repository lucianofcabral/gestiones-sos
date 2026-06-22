"""EliminarGrupo — inactivate a GroupClaim by group_id with referential integrity check."""

from uuid import UUID

from src.domain.ports.repositories import ClaimRepoPort, GroupClaimRepoPort


class EliminarGrupo:
    """Inactivate a GroupClaim by group_id.

    Raises ValueError if any Claim references the group_id.
    Returns True on success, False if the group does not exist.
    """

    def __init__(
        self, group_repo: GroupClaimRepoPort, claim_repo: ClaimRepoPort
    ) -> None:
        self._group_repo = group_repo
        self._claim_repo = claim_repo

    def execute(self, group_id: UUID) -> bool:
        group = self._group_repo.get_by_id(group_id)
        if group is None:
            return False

        if self._claim_repo.exists({"group_id": group_id}):
            raise ValueError(
                f"No se puede eliminar el grupo {group_id}: tiene siniestros asociados"
            )

        return self._group_repo.inactivate(group_id)
