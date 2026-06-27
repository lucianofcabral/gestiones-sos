from uuid import UUID

from pydantic import BaseModel

from src.domain.exceptions import GestionAlreadyExistsError
from src.domain.models.entities import Claim, SosClaim
from src.domain.ports.uow import UnitOfWork


# ── Input ─────────────────────────────────────────────────────────────────────


class RegistrarGestionSOSInput(BaseModel):
    # Datos de Claim (base)
    claim_kind_id: UUID
    group_id: UUID | None = None
    claimer_name: str
    policy_number: str
    plate: str
    claimed_amount: float = 0.0
    comment: str = ""

    # Datos de SosClaim (específicos)
    gestion: int
    category: str = ""
    reason: str = ""
    load_user: str = ""
    response_user: str = ""
    status: str = ""
    itr: int = 0


# ── Output ────────────────────────────────────────────────────────────────────


class RegistrarGestionSOSOutput(BaseModel):
    claim_id: UUID
    sos_claim_id: UUID
    gestion: int
    claimer_name: str
    policy_number: str
    plate: str


# ── Use case ──────────────────────────────────────────────────────────────────


class RegistrarGestionSOS:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(
        self, input_data: RegistrarGestionSOSInput
    ) -> RegistrarGestionSOSOutput:
        with self._uow as uow:
            # Verificar que no exista ya esa gestión SOS
            existing = uow.sos_claims.get_by_number(input_data.gestion)
            if existing is not None:
                raise GestionAlreadyExistsError(
                    f"Ya existe una gestión con el número {input_data.gestion}"
                )

            # Crear el Claim base (SOS no lleva group_id)
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

            # Crear el SosClaim vinculado — atómico con el Claim
            sos_claim = uow.sos_claims.add(
                SosClaim(
                    claim_id=claim.claim_id,
                    gestion=input_data.gestion,
                    category=input_data.category,
                    reason=input_data.reason,
                    load_user=input_data.load_user,
                    response_user=input_data.response_user,
                    status=input_data.status,
                    itr=input_data.itr,
                )
            )

        return RegistrarGestionSOSOutput(
            claim_id=claim.claim_id,
            sos_claim_id=sos_claim.sos_claim_id,
            gestion=sos_claim.gestion,
            claimer_name=claim.claimer_name,
            policy_number=claim.policy_number,
            plate=claim.plate,
        )
