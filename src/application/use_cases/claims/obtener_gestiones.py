"""ObtenerGestiones — list all claims with type-dispatch join for SOS or Grouped data."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from src.domain.ports.repositories import (
    ClaimKindRepoPort,
    ClaimRepoPort,
    GroupClaimRepoPort,
    GroupedClaimRepoPort,
    SosClaimRepoPort,
)


class GestionDTO(BaseModel):
    claim_id: UUID
    gestion_or_reference: str
    claimer_name: str
    policy_number: str
    plate: str
    claimed_amount: float
    claim_kind_name: str
    solved: bool
    active: bool
    created_at: datetime


class ObtenerGestionesInput(BaseModel):
    include_inactive: bool = False


class ObtenerGestionesOutput(BaseModel):
    gestiones: list[GestionDTO]


class ObtenerGestiones:
    """Return all claims with type-appropriate reference and kind name."""

    def __init__(
        self,
        claim_repo: ClaimRepoPort,
        sos_claim_repo: SosClaimRepoPort,
        grouped_claim_repo: GroupedClaimRepoPort,
        group_claim_repo: GroupClaimRepoPort,
        claim_kind_repo: ClaimKindRepoPort,
    ) -> None:
        self._claim_repo = claim_repo
        self._sos_claim_repo = sos_claim_repo
        self._grouped_claim_repo = grouped_claim_repo
        self._group_claim_repo = group_claim_repo
        self._claim_kind_repo = claim_kind_repo

    def execute(self, input_data: ObtenerGestionesInput) -> ObtenerGestionesOutput:
        claims = self._claim_repo.get_all()

        # Filter by active when include_inactive is False
        if not input_data.include_inactive:
            claims = [c for c in claims if c.active]

        # ── Build lookup maps ─────────────────────────────────────────────

        # SOS: last SosClaim per claim_id
        sos_by_claim_id: dict[UUID, Any] = {}
        for sc in self._sos_claim_repo.get_all():
            sos_by_claim_id[sc.claim_id] = sc

        # Grouped: GroupedClaim per claim_id
        grouped_by_claim_id: dict[UUID, Any] = {}
        for gc in self._grouped_claim_repo.get_all():
            grouped_by_claim_id[gc.claim_id] = gc

        # GroupClaim lookup by group_claim_id (group_id)
        group_claims = self._group_claim_repo.get_all()
        group_by_id: dict[UUID, Any] = {g.group_id: g for g in group_claims}

        # ClaimKind lookup by id
        claim_kinds = self._claim_kind_repo.get_all()
        kind_by_id: dict[UUID, str] = {k.claim_kind_id: k.name for k in claim_kinds}

        # ── Assemble DTOs ─────────────────────────────────────────────────

        gestiones = []
        for claim in claims:
            claim_kind_name = kind_by_id.get(claim.claim_kind_id, "")

            sc = sos_by_claim_id.get(claim.claim_id)
            gc = grouped_by_claim_id.get(claim.claim_id)

            if sc is not None:
                # SOS claim
                gestion_or_reference = str(sc.gestion)
            elif gc is not None:
                # Grouped claim — look up the batch external_reference
                group = group_by_id.get(gc.group_claim_id)
                gestion_or_reference = group.external_reference if group else ""
            else:
                gestion_or_reference = ""

            gestiones.append(
                GestionDTO(
                    claim_id=claim.claim_id,
                    gestion_or_reference=gestion_or_reference,
                    claimer_name=claim.claimer_name,
                    policy_number=claim.policy_number,
                    plate=claim.plate,
                    claimed_amount=claim.claimed_amount,
                    claim_kind_name=claim_kind_name,
                    solved=claim.solved,
                    active=claim.active,
                    created_at=claim.created_at,
                )
            )

        return ObtenerGestionesOutput(gestiones=gestiones)
