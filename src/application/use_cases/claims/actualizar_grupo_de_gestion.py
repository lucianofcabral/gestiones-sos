"""ActualizarGrupoDeGestion — change the group assigned to a claim.

Validates the claim and target group exist, persists the change via an
audited UnitOfWork, and returns the updated group info.
"""

from uuid import UUID

from pydantic import BaseModel

from src.domain.exceptions import ClaimNotFoundError
from src.domain.models.entities import Claim
from src.domain.ports.repositories import GroupClaimRepoPort
from src.domain.ports.uow import UnitOfWork


# ── Input ─────────────────────────────────────────────────────────────────────


class ActualizarGrupoDeGestionInput(BaseModel):
    claim_id: UUID
    new_group_id: UUID | None = None


# ── Output ────────────────────────────────────────────────────────────────────


class ActualizarGrupoDeGestionOutput(BaseModel):
    claim_id: UUID
    old_group_id: UUID | None
    new_group_id: UUID | None
    group_name: str = ""


# ── Use case ──────────────────────────────────────────────────────────────────


class ActualizarGrupoDeGestion:
    """Change the group assignment of a claim with audit trail."""

    def __init__(
        self,
        uow: UnitOfWork,
        group_claim_repo: GroupClaimRepoPort,
    ) -> None:
        self._uow = uow
        self._group_claim_repo = group_claim_repo

    def execute(
        self, input_data: ActualizarGrupoDeGestionInput
    ) -> ActualizarGrupoDeGestionOutput:
        with self._uow as uow:
            # 1. Validate claim exists
            claim = uow.claims.get_by_id(input_data.claim_id)
            if claim is None:
                raise ClaimNotFoundError(
                    f"Claim with id {input_data.claim_id} not found"
                )

            # 2. Validate target group exists (skip if removing from group)
            old_group_id = claim.group_id
            group_name = ""
            if input_data.new_group_id is not None:
                new_group = self._group_claim_repo.get_by_id(
                    input_data.new_group_id
                )
                if new_group is None:
                    raise ValueError(
                        f"No existe un grupo con id {input_data.new_group_id}"
                    )
                group_name = new_group.name

            # 3. Persist the change via audited UoW
            updated = claim.model_copy(
                update={"group_id": input_data.new_group_id}
            )
            uow.claims.update(input_data.claim_id, updated)

        return ActualizarGrupoDeGestionOutput(
            claim_id=input_data.claim_id,
            old_group_id=old_group_id,
            new_group_id=input_data.new_group_id,
            group_name=group_name,
        )
