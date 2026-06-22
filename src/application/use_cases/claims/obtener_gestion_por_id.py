"""ObtenerGestionPorId — fetch a single claim with type-dispatched related data."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.exceptions import ClaimNotFoundError
from src.domain.ports.repositories import (
    ClaimKindRepoPort,
    ClaimRepoPort,
    GroupClaimRepoPort,
    GroupedClaimRepoPort,
    PaymentRepoPort,
    SosClaimRepoPort,
)


class ObtenerGestionPorIdInput(BaseModel):
    claim_id: UUID


class SosClaimDetailDTO(BaseModel):
    sos_claim_id: UUID
    gestion: int
    category: str
    reason: str
    status: str
    load_user: str
    response_user: str
    itr: int


class GroupedClaimDetailDTO(BaseModel):
    group_claim_id: UUID
    external_reference: str
    notes: str
    created_at: datetime


class PaymentDTO(BaseModel):
    payment_id: UUID
    amount: float
    created_date: datetime
    active: bool


class GestionDetalleDTO(BaseModel):
    claim_id: UUID
    claimer_name: str
    policy_number: str
    plate: str
    claimed_amount: float
    comment: str
    solved: bool
    active: bool
    created_at: datetime
    group_name: str
    claim_kind_name: str
    sos_records: list[SosClaimDetailDTO]
    grouped_data: GroupedClaimDetailDTO | None = None
    payments: list[PaymentDTO]


class ObtenerGestionPorId:
    """Return a single claim with type-dispatched detail sections."""

    def __init__(
        self,
        claim_repo: ClaimRepoPort,
        sos_claim_repo: SosClaimRepoPort,
        group_claim_repo: GroupClaimRepoPort,
        claim_kind_repo: ClaimKindRepoPort,
        payment_repo: PaymentRepoPort,
        grouped_claim_repo: GroupedClaimRepoPort,
    ) -> None:
        self._claim_repo = claim_repo
        self._sos_claim_repo = sos_claim_repo
        self._group_claim_repo = group_claim_repo
        self._claim_kind_repo = claim_kind_repo
        self._payment_repo = payment_repo
        self._grouped_claim_repo = grouped_claim_repo

    def execute(self, input_data: ObtenerGestionPorIdInput) -> GestionDetalleDTO:
        # 1. Fetch claim — raises ClaimNotFoundError if missing
        claim = self._claim_repo.get_by_id(input_data.claim_id)
        if claim is None:
            raise ClaimNotFoundError(f"Claim with id {input_data.claim_id} not found")

        # 2. Type-dispatch: check if this is a Grouped claim
        grouped_claim = self._grouped_claim_repo.get_by_claim_id(claim.claim_id)
        if grouped_claim is not None:
            # ── Grouped claim path ─────────────────────────────────────────
            sos_records: list[SosClaimDetailDTO] = []

            # Fetch the GroupClaim batch for external_reference
            group = self._group_claim_repo.get_by_id(grouped_claim.group_claim_id)
            if group is None:
                raise ClaimNotFoundError(
                    f"GroupClaim for grouped claim {claim.claim_id} not found"
                )

            grouped_data = GroupedClaimDetailDTO(
                group_claim_id=grouped_claim.group_claim_id,
                external_reference=group.external_reference,
                notes=grouped_claim.notes,
                created_at=grouped_claim.created_at,
            )
        else:
            # ── SOS (or other type) path ───────────────────────────────────
            sos_claim_rows = self._sos_claim_repo.get_claims_by_claim_id(claim.claim_id)
            sos_records = [
                SosClaimDetailDTO(
                    sos_claim_id=sc.sos_claim_id,
                    gestion=sc.gestion,
                    category=sc.category,
                    reason=sc.reason,
                    status=sc.status,
                    load_user=sc.load_user,
                    response_user=sc.response_user,
                    itr=sc.itr,
                )
                for sc in sos_claim_rows
            ]
            grouped_data = None

        # 3. Fetch group name (None guard → empty string)
        group = self._group_claim_repo.get_by_claim_id(claim.claim_id)
        group_name = group.name if group is not None else ""

        # 4. Fetch claim kind name (None guard → empty string)
        kind = self._claim_kind_repo.get_by_id(claim.claim_kind_id)
        claim_kind_name = kind.name if kind is not None else ""

        # 5. Fetch payments (may be empty)
        payments = self._payment_repo.get_by_claim_id(claim.claim_id)

        # 6. Assemble and return DTO
        return GestionDetalleDTO(
            claim_id=claim.claim_id,
            claimer_name=claim.claimer_name,
            policy_number=claim.policy_number,
            plate=claim.plate,
            claimed_amount=claim.claimed_amount,
            comment=claim.comment,
            solved=claim.solved,
            active=claim.active,
            created_at=claim.created_at,
            group_name=group_name,
            claim_kind_name=claim_kind_name,
            sos_records=sos_records,
            grouped_data=grouped_data,
            payments=[
                PaymentDTO(
                    payment_id=p.payment_id,
                    amount=p.amount,
                    created_date=p.created_date,
                    active=p.active,
                )
                for p in payments
            ],
        )
