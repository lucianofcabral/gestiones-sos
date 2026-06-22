"""RegistrarGroupedClaim — create a Claim + GroupedClaim atomically via UoW."""

from uuid import UUID

from pydantic import BaseModel

from src.domain.models.entities import Claim, GroupedClaim
from src.domain.ports.uow import UnitOfWork


# ── Input ─────────────────────────────────────────────────────────────────────


class RegistrarGroupedClaimInput(BaseModel):
    # Datos de Claim (base)
    claim_kind_id: UUID
    group_id: UUID
    claimer_name: str
    policy_number: str
    plate: str
    claimed_amount: float = 0.0
    comment: str = ""

    # Datos de GroupedClaim (específicos)
    group_claim_id: UUID
    notes: str = ""


# ── Output ────────────────────────────────────────────────────────────────────


class RegistrarGroupedClaimOutput(BaseModel):
    claim_id: UUID
    grouped_claim_id: UUID
    claimer_name: str
    policy_number: str
    plate: str


# ── Use case ──────────────────────────────────────────────────────────────────


class RegistrarGroupedClaim:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(
        self, input_data: RegistrarGroupedClaimInput
    ) -> RegistrarGroupedClaimOutput:
        with self._uow as uow:
            # Crear el Claim base
            claim = uow.claims.add(
                Claim(
                    claim_kind_id=input_data.claim_kind_id,
                    group_id=input_data.group_id,
                    claimer_name=input_data.claimer_name,
                    policy_number=input_data.policy_number,
                    plate=input_data.plate,
                    claimed_amount=input_data.claimed_amount,
                    comment=input_data.comment,
                )
            )

            # Crear el GroupedClaim vinculado — atómico con el Claim
            grouped_claim = uow.grouped_claims.add(
                GroupedClaim(
                    claim_id=claim.claim_id,
                    group_claim_id=input_data.group_claim_id,
                    notes=input_data.notes,
                )
            )

        return RegistrarGroupedClaimOutput(
            claim_id=claim.claim_id,
            grouped_claim_id=grouped_claim.grouped_claim_id,
            claimer_name=claim.claimer_name,
            policy_number=claim.policy_number,
            plate=claim.plate,
        )
