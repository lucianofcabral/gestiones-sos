"""ActualizarGestion — update all editable fields of a claim.

Supports changing group_id (including removing it), claimer_name,
policy_number, plate, claimed_amount, comment, solved, and active.
Audited via UnitOfWork.
"""

from uuid import UUID

from pydantic import BaseModel

from src.domain.exceptions import ClaimNotFoundError
from src.domain.models.entities import Claim
from src.domain.ports.repositories import GroupClaimRepoPort
from src.domain.ports.uow import UnitOfWork


# ── Input ─────────────────────────────────────────────────────────────────────


class ActualizarGestionInput(BaseModel):
    claim_id: UUID
    group_id: UUID | None = None
    claimer_name: str
    policy_number: str
    plate: str
    claimed_amount: float
    comment: str = ""
    solved: bool = False
    active: bool = True


# ── Output ────────────────────────────────────────────────────────────────────


class ActualizarGestionOutput(BaseModel):
    claim_id: UUID
    group_id: UUID | None
    claimer_name: str
    policy_number: str
    plate: str
    claimed_amount: float
    comment: str
    solved: bool
    active: bool


# ── Use case ──────────────────────────────────────────────────────────────────


class ActualizarGestion:
    """Update all editable fields of a claim with audit trail."""

    def __init__(
        self,
        uow: UnitOfWork,
        group_claim_repo: GroupClaimRepoPort,
    ) -> None:
        self._uow = uow
        self._group_claim_repo = group_claim_repo

    def execute(self, input_data: ActualizarGestionInput) -> ActualizarGestionOutput:
        with self._uow as uow:
            # 1. Validate claim exists
            claim = uow.claims.get_by_id(input_data.claim_id)
            if claim is None:
                raise ClaimNotFoundError(
                    f"Claim with id {input_data.claim_id} not found"
                )

            # 2. Validate target group exists if changing to a non-None value
            if input_data.group_id is not None:
                new_group = self._group_claim_repo.get_by_id(input_data.group_id)
                if new_group is None:
                    raise ValueError(
                        f"No existe un grupo con id {input_data.group_id}"
                    )

            # 3. Persist via audited UoW
            updated = claim.model_copy(update=input_data.model_dump())
            uow.claims.update(input_data.claim_id, updated)

        return ActualizarGestionOutput(
            claim_id=input_data.claim_id,
            group_id=input_data.group_id,
            claimer_name=input_data.claimer_name,
            policy_number=input_data.policy_number,
            plate=input_data.plate,
            claimed_amount=input_data.claimed_amount,
            comment=input_data.comment,
            solved=input_data.solved,
            active=input_data.active,
        )
