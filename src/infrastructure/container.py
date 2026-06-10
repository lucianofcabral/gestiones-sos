import os
from typing import Any
from uuid import UUID

from src.adapters.auth import JwtService, PasswordAdapter
from src.adapters.persistence.sqlalchemy_claim_repository import (
    SqlAlchemyClaimRepository,
)
from src.adapters.persistence.sqlalchemy_ncpayment_repository import (
    SqlAlchemyNcPaymentRepository,
)
from src.adapters.persistence.sqlalchemy_payment_repository import (
    SqlAlchemyPaymentRepository,
)
from src.adapters.persistence.sqlalchemy_period_repository import (
    SqlAlchemyPeriodRepository,
)
from src.adapters.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository
from src.application.use_cases.claims.eliminar_gestion_sos import EliminarGestionSOS
from src.application.use_cases.payments.activar_nc import ActivarNotaCredito
from src.application.use_cases.payments.activar_pago import ActivarPago
from src.application.use_cases.payments.actualizar_pago import ActualizarPago
from src.application.use_cases.payments.inactivar_nc import InactivarNotaCredito
from src.application.use_cases.payments.inactivar_pago import InactivarPago
from src.application.use_cases.payments.marcar_nc_entregada import (
    MarcarNotaCreditoEntregada,
)
from src.application.use_cases.payments.obtener_ncs import ObtenerNotasCredito
from src.application.use_cases.payments.obtener_pagos import ObtenerPagos
from src.application.use_cases.payments.registrar_nc import RegistrarNotaCredito
from src.application.use_cases.payments.registrar_pago import RegistrarPago
from src.domain.models.entities import Agent, Invoice, PaymentVia
from src.domain.ports.repositories import (
    BillingRepoPort,
    ClaimRepoPort,
    NcPaymentRepoPort,
    PaymentRepoPort,
    PeriodRepoPort,
    UserRepoPort,
)
from src.domain.services.can_activate_payment import CanActivatePaymentService
from src.domain.services.can_inactivate_payment import CanInactivatePaymentService
from src.domain.services.payment_update_rules import PaymentUpdateRules
from src.ui.routes.auth import AuthRouter


# ── Repo factories ────────────────────────────────────────────────────────────


def _build_user_repo() -> UserRepoPort:
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return SqlAlchemyUserRepository()


def _build_claim_repo() -> ClaimRepoPort:
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return SqlAlchemyClaimRepository()


def _build_period_repo() -> PeriodRepoPort:
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return SqlAlchemyPeriodRepository()


def _build_payment_repo() -> PaymentRepoPort:
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return SqlAlchemyPaymentRepository()


def _build_nc_payment_repo() -> NcPaymentRepoPort:
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return SqlAlchemyNcPaymentRepository()


# ── Stub repos for dependencies without SQLAlchemy implementations ────────────


class _StubBillingRepository:
    """Stub BillingRepoPort — always returns no invoices.

    Used because no SQLAlchemyBillingRepository exists yet.
    """

    def add(self, model: Invoice) -> Invoice:
        return model

    def get_by_id(self, id: UUID) -> Invoice | None:
        return None

    def get_all(self) -> list[Invoice]:
        return []

    def delete(self, id: UUID) -> None:
        pass

    def update(self, id: UUID, model: Invoice) -> bool:
        return False

    def exists(self, data: dict[str, Any]) -> bool:
        return False

    def get_by_ids(self, ids: list[UUID]) -> list[Invoice]:
        return []

    def get_by_document_id(self, document_id: UUID) -> list[Invoice]:
        return []

    def get_by_document(self, document: bytes) -> list[Invoice]:
        return []

    def get_by_period_id(self, period_id: UUID) -> list[Invoice]:
        return []


class _StubAgentRepository:
    """Stub AgentRepoPort — returns None for all lookups.

    Used because no SqlAlchemyAgentRepository exists yet.
    """

    def add(self, model: Agent) -> Agent:
        return model

    def get_by_id(self, id: UUID) -> Agent | None:
        return None

    def get_all(self) -> list[Agent]:
        return []

    def delete(self, id: UUID) -> None:
        pass

    def update(self, id: UUID, model: Agent) -> bool:
        return False

    def exists(self, data: dict[str, Any]) -> bool:
        return False

    def get_by_ids(self, ids: list[UUID]) -> list[Agent]:
        return []

    def activate(self, id: UUID) -> bool:
        return False

    def inactivate(self, id: UUID) -> bool:
        return False

    def get_by_name(self, name: str) -> Agent | None:
        return None

    def get_sm(self) -> Agent | None:
        return None

    def get_prestador(self) -> Agent | None:
        return None

    def get_sos(self) -> Agent | None:
        return None

    def get_asegurado(self) -> Agent | None:
        return None


class _StubPaymentViaRepository:
    """Stub PaymentViaRepoPort — returns None for all lookups.

    Used because no SqlAlchemyPaymentViaRepository exists yet.
    """

    def add(self, model: PaymentVia) -> PaymentVia:
        return model

    def get_by_id(self, id: UUID) -> PaymentVia | None:
        return None

    def get_all(self) -> list[PaymentVia]:
        return []

    def delete(self, id: UUID) -> None:
        pass

    def update(self, id: UUID, model: PaymentVia) -> bool:
        return False

    def exists(self, data: dict[str, Any]) -> bool:
        return False

    def get_by_ids(self, ids: list[UUID]) -> list[PaymentVia]:
        return []

    def activate(self, id: UUID) -> bool:
        return False

    def inactivate(self, id: UUID) -> bool:
        return False

    def get_by_name(self, name: str) -> PaymentVia | None:
        return None

    def get_transferencia(self) -> PaymentVia | None:
        return None

    def get_nc(self) -> PaymentVia | None:
        return None


# ── Container ─────────────────────────────────────────────────────────────────


class Container:
    _instance: "Container | None" = None

    def __init__(self):
        jwt_secret = os.environ.get("JWT_SECRET")
        if not jwt_secret:
            raise RuntimeError("JWT_SECRET environment variable is not set")

        self._user_repo = _build_user_repo()
        self._claim_repo = _build_claim_repo()
        self._period_repo = _build_period_repo()
        self._payment_repo = _build_payment_repo()
        self._nc_payment_repo = _build_nc_payment_repo()
        self._password_adapter = PasswordAdapter()
        self._jwt_service = JwtService(secret=jwt_secret)

        # Stub repos for unimplemented adapters
        self._billing_repo: BillingRepoPort = _StubBillingRepository()
        self._agent_repo = _StubAgentRepository()
        self._payment_via_repo = _StubPaymentViaRepository()

        # Domain services
        self._can_inactivate_svc = CanInactivatePaymentService(
            nc_payment_repo=self._nc_payment_repo,
            billing_repo=self._billing_repo,
        )
        self._payment_update_rules = PaymentUpdateRules(
            nc_payment_repo=self._nc_payment_repo,
            payment_via_repo=self._payment_via_repo,
        )
        self._can_activate_svc = CanActivatePaymentService(
            claim_repo=self._claim_repo,
        )

        # Use cases
        self._eliminar_gestion_sos = EliminarGestionSOS(
            claim_repo=self._claim_repo,
            payment_repo=self._payment_repo,
        )
        self._registrar_pago = RegistrarPago(
            payment_repo=self._payment_repo,
            nc_payment_repo=self._nc_payment_repo,
            payment_via_repo=self._payment_via_repo,
            agent_repo=self._agent_repo,
        )
        self._inactivar_pago = InactivarPago(
            payment_repo=self._payment_repo,
            can_inactivate_svc=self._can_inactivate_svc,
        )
        self._actualizar_pago = ActualizarPago(
            payment_repo=self._payment_repo,
            update_rules=self._payment_update_rules,
        )
        self._activar_pago = ActivarPago(
            payment_repo=self._payment_repo,
            can_activate_svc=self._can_activate_svc,
        )
        self._obtener_pagos = ObtenerPagos(payment_repo=self._payment_repo)
        self._registrar_nc = RegistrarNotaCredito(nc_payment_repo=self._nc_payment_repo)
        self._obtener_ncs = ObtenerNotasCredito(nc_payment_repo=self._nc_payment_repo)
        self._marcar_nc_entregada = MarcarNotaCreditoEntregada(
            nc_payment_repo=self._nc_payment_repo
        )
        self._inactivar_nc = InactivarNotaCredito(nc_payment_repo=self._nc_payment_repo)
        self._activar_nc = ActivarNotaCredito(nc_payment_repo=self._nc_payment_repo)

        self._auth_router = AuthRouter(
            user_repo=self._user_repo,
            password_port=self._password_adapter,
            token_port=self._jwt_service,
        )

    @classmethod
    def get_instance(cls) -> "Container":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def user_repo(self) -> UserRepoPort:
        return self._user_repo

    @property
    def claim_repo(self) -> ClaimRepoPort:
        return self._claim_repo

    @property
    def period_repo(self) -> PeriodRepoPort:
        return self._period_repo

    @property
    def payment_repo(self) -> PaymentRepoPort:
        return self._payment_repo

    @property
    def nc_payment_repo(self) -> NcPaymentRepoPort:
        return self._nc_payment_repo

    @property
    def billing_repo(self) -> BillingRepoPort:
        return self._billing_repo

    @property
    def password_adapter(self) -> PasswordAdapter:
        return self._password_adapter

    @property
    def jwt_service(self) -> JwtService:
        return self._jwt_service

    @property
    def can_inactivate_svc(self) -> CanInactivatePaymentService:
        return self._can_inactivate_svc

    @property
    def payment_update_rules(self) -> PaymentUpdateRules:
        return self._payment_update_rules

    @property
    def can_activate_svc(self) -> CanActivatePaymentService:
        return self._can_activate_svc

    @property
    def eliminar_gestion_sos(self) -> EliminarGestionSOS:
        return self._eliminar_gestion_sos

    @property
    def registrar_pago(self) -> RegistrarPago:
        return self._registrar_pago

    @property
    def inactivar_pago(self) -> InactivarPago:
        return self._inactivar_pago

    @property
    def actualizar_pago(self) -> ActualizarPago:
        return self._actualizar_pago

    @property
    def activar_pago(self) -> ActivarPago:
        return self._activar_pago

    @property
    def obtener_pagos(self) -> ObtenerPagos:
        return self._obtener_pagos

    @property
    def registrar_nc(self) -> RegistrarNotaCredito:
        return self._registrar_nc

    @property
    def obtener_ncs(self) -> ObtenerNotasCredito:
        return self._obtener_ncs

    @property
    def marcar_nc_entregada(self) -> MarcarNotaCreditoEntregada:
        return self._marcar_nc_entregada

    @property
    def inactivar_nc(self) -> InactivarNotaCredito:
        return self._inactivar_nc

    @property
    def activar_nc(self) -> ActivarNotaCredito:
        return self._activar_nc

    @property
    def auth_router(self) -> AuthRouter:
        return self._auth_router


def get_container() -> Container:
    return Container.get_instance()
