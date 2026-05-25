from enum import Enum


class DocumentTypeEnum(str, Enum):
    USER = "user"
    PERIOD = "period"
    INVOICE = "invoice"
    AGENT = "agent"
    PAYMENT_VIA = "payment_via"
    CLAIM_KIND = "claim_kind"
    CLAIM = "claim"
    SOS_CLAIM = "sos_claim"
    GROUP_CLAIM = "group_claim"
    PAYMENT = "payment"
    CREDIT_NOTE = "credit_note"


class UserStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
