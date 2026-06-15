import calendar
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field

from src.domain.enums import DocumentTypeEnum

_MESES_ES = [
    "",
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]


class User(BaseModel):
    user_id: UUID = Field(default_factory=uuid4)
    user_name: str = Field(min_length=3, max_length=255)
    user_email: EmailStr = Field(...)
    password_hash: str = Field(min_length=1, max_length=255)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)


class Document(BaseModel):
    document_id: UUID = Field(default_factory=uuid4)
    document_hash: str = Field(min_length=1, max_length=64)
    type: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    size: int = Field(0, ge=0)
    mime: str = Field("", max_length=100)
    description: str = Field("", max_length=500)
    uploaded_by: UUID | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class DocumentEntity(BaseModel):
    document_id: UUID = Field(default_factory=uuid4)
    entity_type: DocumentTypeEnum
    entity_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.now)


class Period(BaseModel):
    period_id: UUID = Field(default_factory=uuid4)
    year: int = Field(0, ge=2020, lt=2040)
    month: int = Field(0, ge=1, le=12)
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def period_number(self) -> int:
        return self.year * 100 + self.month

    @property
    def period_name(self) -> str:
        return f"{_MESES_ES[self.month].capitalize()} {self.year}"

    @property
    def first_day(self) -> date:
        return date(self.year, self.month, 1)

    @property
    def last_day(self) -> date:
        last_day = calendar.monthrange(self.year, self.month)[1]
        return date(self.year, self.month, last_day)

    @property
    def next_period(self) -> dict[str, int]:
        d: date = self.first_day + timedelta(days=10)
        next_month = d + timedelta(days=25)
        return {"year": next_month.year, "month": next_month.month}


class Invoice(BaseModel):
    invoice_id: UUID = Field(default_factory=uuid4)
    invoice_number: str = Field(min_length=1, max_length=50)
    period_id: UUID = Field(default_factory=uuid4)
    emited_date: datetime
    amount: float = Field(gt=0)
    created_at: datetime = Field(default_factory=datetime.now)


class Agent(BaseModel):
    agent_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=100)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)


class PaymentVia(BaseModel):
    payment_via_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=100)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)


class ClaimKind(BaseModel):
    claim_kind_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=100)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)


class Claim(BaseModel):
    claim_id: UUID = Field(default_factory=uuid4)
    claim_kind_id: UUID = Field(default_factory=uuid4)
    group_id: UUID = Field(default_factory=uuid4)
    claimer_name: str = Field(min_length=1, max_length=100)
    policy_number: str = Field(min_length=1, max_length=25)
    plate: str = Field(min_length=6)
    claimed_amount: float = Field(0, ge=0)
    comment: str = Field("", max_length=255)
    solved: bool = False
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class SosClaim(BaseModel):
    sos_claim_id: UUID = Field(default_factory=uuid4)
    claim_id: UUID = Field(default_factory=uuid4)
    gestion: int = Field(gt=0)
    category: str = ""
    reason: str = ""
    load_user: str = ""
    response_user: str = ""
    status: str = ""
    itr: int = 0


class GroupClaim(BaseModel):
    group_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=100)
    external_reference: str = Field(min_length=1, max_length=100)
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class GroupedClaim(BaseModel):
    grouped_claim_id: UUID = Field(default_factory=uuid4)
    claim_id: UUID = Field(default_factory=uuid4)
    group_claim_id: UUID = Field(default_factory=uuid4)
    notes: str = Field("", max_length=500)
    created_at: datetime = Field(default_factory=datetime.now)


class Payment(BaseModel):
    payment_id: UUID = Field(default_factory=uuid4)
    claim_id: UUID = Field(default_factory=uuid4)
    payer_id: UUID = Field(default_factory=uuid4)
    payment_via_id: UUID = Field(default_factory=uuid4)
    payee_id: UUID = Field(default_factory=uuid4)
    amount: float = Field(gt=0)
    active: bool = True
    created_date: datetime = Field(default_factory=datetime.now)


class CreditNote(BaseModel):
    nc_payment_id: UUID = Field(default_factory=uuid4)
    payment_id: UUID = Field(default_factory=uuid4)
    period_id: UUID = Field(default_factory=uuid4)
    delivered: bool = Field(False)
    active: bool = True
    created_date: datetime = Field(default_factory=datetime.now)
