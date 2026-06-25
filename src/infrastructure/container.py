import os

from src.infrastructure.config import Settings

from src.adapters.persistence.sqlalchemy_document_repository import (
    SqlAlchemyDocumentRepository,
)
from src.adapters.auth import JwtService, PasswordAdapter
from src.adapters.persistence.sqlalchemy_agent_repository import (
    SqlAlchemyAgentRepository,
)
from src.adapters.persistence.sqlalchemy_claim_kind_repository import (
    SqlAlchemyClaimKindRepository,
)
from src.adapters.persistence.sqlalchemy_claim_repository import (
    SqlAlchemyClaimRepository,
)
from src.adapters.persistence.sqlalchemy_sos_claim_repository import (
    SqlAlchemySosClaimRepository,
)
from src.adapters.persistence.sqlalchemy_group_claim_repository import (
    SqlAlchemyGroupClaimRepository,
)
from src.adapters.persistence.sqlalchemy_grouped_claim_repository import (
    SqlAlchemyGroupedClaimRepository,
)
from src.adapters.persistence.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from src.adapters.persistence.sqlalchemy_ncpayment_repository import (
    SqlAlchemyNcPaymentRepository,
)
from src.adapters.persistence.sqlalchemy_payment_repository import (
    SqlAlchemyPaymentRepository,
)
from src.adapters.persistence.sqlalchemy_payment_via_repository import (
    SqlAlchemyPaymentViaRepository,
)
from src.adapters.persistence.sqlalchemy_period_repository import (
    SqlAlchemyPeriodRepository,
)
from src.adapters.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository
from src.adapters.persistence.sqlalchemy_billing_repository import (
    SqlAlchemyBillingRepository,
)
from src.application.use_cases.billing.eliminar_factura import EliminarFactura
from src.application.use_cases.billing.obtener_factura import ObtenerFactura
from src.application.use_cases.billing.obtener_facturas import ObtenerFacturas
from src.application.use_cases.billing.obtener_total_facturacion import (
    ObtenerTotalFacturacion,
)
from src.application.use_cases.billing.registrar_factura import RegistrarFactura
from src.application.use_cases.periods.crear_periodo import CrearPeriodo
from src.application.use_cases.periods.eliminar_periodo import EliminarPeriodo
from src.application.use_cases.periods.listar_periodos import ListarPeriodos
from src.application.use_cases.documents.subir_documento import SubirDocumento
from src.application.use_cases.documents.descargar_documento import DescargarDocumento
from src.application.use_cases.documents.obtener_documentos import ObtenerDocumentos
from src.application.use_cases.claims.actualizar_grupo import ActualizarGrupo
from src.application.use_cases.claims.actualizar_grupo_de_gestion import (
    ActualizarGrupoDeGestion,
)
from src.application.use_cases.claims.eliminar_gestion_sos import EliminarGestionSOS
from src.application.use_cases.claims.obtener_gestion_por_id import (
    ObtenerGestionPorId,
)
from src.application.use_cases.claims.obtener_gestiones import ObtenerGestiones
from src.application.use_cases.claims.eliminar_grupo import EliminarGrupo
from src.application.use_cases.claims.obtener_claim_kinds import ObtenerClaimKinds
from src.application.use_cases.claims.obtener_grupos import ObtenerGrupos
from src.application.use_cases.claims.registrar_gestion_sos import RegistrarGestionSOS
from src.application.use_cases.claims.registrar_grouped_claim import (
    RegistrarGroupedClaim,
)
from src.application.use_cases.claims.eliminar_grouped_claim import (
    EliminarGroupedClaim,
)
from src.application.use_cases.claims.importar_gestiones_sos import ImportarGestionSOS
from src.application.use_cases.claims.registrar_grupo import RegistrarGrupo
from src.application.use_cases.payments.activar_pago import ActivarPago
from src.application.use_cases.payments.actualizar_pago import ActualizarPago
from src.application.use_cases.payments.inactivar_pago import InactivarPago
from src.application.use_cases.payments.marcar_nc_entregada import (
    MarcarNotaCreditoEntregada,
)
from src.application.use_cases.payments.obtener_ncs import ObtenerNotasCredito
from src.application.use_cases.payments.obtener_pagos import ObtenerPagos
from src.application.use_cases.payments.registrar_nc import RegistrarNotaCredito
from src.application.use_cases.payments.registrar_pago import RegistrarPago
from src.domain.ports.repositories import (
    BillingRepoPort,
    ClaimKindRepoPort,
    ClaimRepoPort,
    DocumentRepoPort,
    GroupClaimRepoPort,
    GroupedClaimRepoPort,
    NcPaymentRepoPort,
    PaymentRepoPort,
    PeriodRepoPort,
    SosClaimRepoPort,
    UserRepoPort,
)
from src.infrastructure.storage.filesystem_storage import FilesystemStorageService
from src.domain.services.can_activate_payment import CanActivatePaymentService
from src.domain.services.can_inactivate_payment import CanInactivatePaymentService
from src.domain.services.payment_update_rules import PaymentUpdateRules
from src.application.services.audit_context import set_audit_user
from src.application.services.audit_wrapper import AuditRepositoryWrapper
from src.adapters.persistence.sqlalchemy_audit_repository import (
    SqlAlchemyAuditRepository,
)
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


def _build_sos_claim_repo() -> SosClaimRepoPort:
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return SqlAlchemySosClaimRepository()


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


def _build_agent_repo():
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return SqlAlchemyAgentRepository()


def _build_payment_via_repo():
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return SqlAlchemyPaymentViaRepository()


def _build_claim_kind_repo():
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return SqlAlchemyClaimKindRepository()


def _build_document_repo() -> DocumentRepoPort:
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return SqlAlchemyDocumentRepository()


def _build_group_claim_repo() -> GroupClaimRepoPort:
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return SqlAlchemyGroupClaimRepository()


def _build_grouped_claim_repo() -> GroupedClaimRepoPort:
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return SqlAlchemyGroupedClaimRepository()


def _build_billing_repo():
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return SqlAlchemyBillingRepository()


def _build_storage_service(settings: Settings) -> FilesystemStorageService:
    return FilesystemStorageService(base_path=settings.storage_path)


# ── Container ─────────────────────────────────────────────────────────────────


class Container:
    _instance: "Container | None" = None

    def __init__(self):
        self._settings = Settings()

        jwt_secret = self._settings.jwt_secret
        if not jwt_secret:
            raise RuntimeError("JWT_SECRET environment variable is not set")

        self._user_repo = _build_user_repo()
        self._claim_repo = _build_claim_repo()
        self._sos_claim_repo = _build_sos_claim_repo()
        self._period_repo = _build_period_repo()
        self._payment_repo = _build_payment_repo()
        self._nc_payment_repo = _build_nc_payment_repo()
        self._password_adapter = PasswordAdapter()
        self._jwt_service = JwtService(secret=jwt_secret)

        self._billing_repo = _build_billing_repo()
        self._agent_repo = _build_agent_repo()
        self._payment_via_repo = _build_payment_via_repo()
        self._claim_kind_repo = _build_claim_kind_repo()
        self._group_claim_repo = _build_group_claim_repo()
        self._grouped_claim_repo = _build_grouped_claim_repo()

        # ── Audit ────────────────────────────────────────────────────────────────
        self._audit_repo = SqlAlchemyAuditRepository()
        self._payment_repo = AuditRepositoryWrapper(
            inner=self._payment_repo,
            audit_repo=self._audit_repo,
            entity_type="payment",
        )
        self._billing_repo = AuditRepositoryWrapper(
            inner=self._billing_repo,
            audit_repo=self._audit_repo,
            entity_type="invoice",
        )
        self._group_claim_repo = AuditRepositoryWrapper(
            inner=self._group_claim_repo,
            audit_repo=self._audit_repo,
            entity_type="group_claim",
        )
        self._period_repo = AuditRepositoryWrapper(
            inner=self._period_repo,
            audit_repo=self._audit_repo,
            entity_type="period",
        )
        self._agent_repo = AuditRepositoryWrapper(
            inner=self._agent_repo,
            audit_repo=self._audit_repo,
            entity_type="agent",
        )
        self._payment_via_repo = AuditRepositoryWrapper(
            inner=self._payment_via_repo,
            audit_repo=self._audit_repo,
            entity_type="payment_via",
        )
        self._claim_kind_repo = AuditRepositoryWrapper(
            inner=self._claim_kind_repo,
            audit_repo=self._audit_repo,
            entity_type="claim_kind",
        )

        # Document repos and use cases
        self._document_repo = _build_document_repo()
        self._document_repo = AuditRepositoryWrapper(
            inner=self._document_repo,
            audit_repo=self._audit_repo,
            entity_type="document",
        )
        self._storage_service = _build_storage_service(self._settings)
        self._subir_documento = SubirDocumento(
            self._document_repo, self._storage_service
        )
        self._descargar_documento = DescargarDocumento(
            self._document_repo, self._storage_service
        )
        self._obtener_documentos = ObtenerDocumentos(self._document_repo)

        # GroupClaim use cases
        self._registrar_grupo = RegistrarGrupo(self._group_claim_repo)
        self._obtener_grupos = ObtenerGrupos(self._group_claim_repo)
        self._eliminar_grupo = EliminarGrupo(
            group_repo=self._group_claim_repo, claim_repo=self._claim_repo
        )
        self._actualizar_grupo = ActualizarGrupo(self._group_claim_repo)
        self._actualizar_grupo_de_gestion = ActualizarGrupoDeGestion(
            uow=SqlAlchemyUnitOfWork(enable_audit=True),
            group_claim_repo=self._group_claim_repo,
        )

        # Claim registration use cases
        self._obtener_claim_kinds = ObtenerClaimKinds(self._claim_kind_repo)
        self._registrar_gestion_sos = RegistrarGestionSOS(SqlAlchemyUnitOfWork(enable_audit=True))
        self._registrar_grouped_claim = RegistrarGroupedClaim(SqlAlchemyUnitOfWork(enable_audit=True))

        # Billing use cases
        self._registrar_factura = RegistrarFactura(self._billing_repo)
        self._obtener_facturas = ObtenerFacturas(self._billing_repo)
        self._obtener_factura = ObtenerFactura(self._billing_repo)
        self._eliminar_factura = EliminarFactura(
            self._billing_repo, self._document_repo
        )
        self._obtener_total_facturacion = ObtenerTotalFacturacion(self._period_repo)

        # Period use cases
        self._crear_periodo = CrearPeriodo(self._period_repo)
        self._listar_periodos = ListarPeriodos(self._period_repo)
        self._eliminar_periodo = EliminarPeriodo(
            self._period_repo, self._billing_repo, self._nc_payment_repo
        )

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
        self._importar_gestiones_sos = ImportarGestionSOS(
            uow_cls=SqlAlchemyUnitOfWork,
            claim_kind_repo=self._claim_kind_repo,
            group_claim_repo=self._group_claim_repo,
        )
        self._eliminar_gestion_sos = EliminarGestionSOS(
            claim_repo=self._claim_repo,
            payment_repo=self._payment_repo,
        )
        self._eliminar_grouped_claim = EliminarGroupedClaim(
            uow=SqlAlchemyUnitOfWork(enable_audit=True),
            payment_repo=self._payment_repo,
        )
        self._obtener_gestiones = ObtenerGestiones(
            claim_repo=self._claim_repo,
            sos_claim_repo=self._sos_claim_repo,
            grouped_claim_repo=self._grouped_claim_repo,
            group_claim_repo=self._group_claim_repo,
            claim_kind_repo=self._claim_kind_repo,
        )
        self._obtener_gestion_por_id = ObtenerGestionPorId(
            claim_repo=self._claim_repo,
            sos_claim_repo=self._sos_claim_repo,
            group_claim_repo=self._group_claim_repo,
            claim_kind_repo=self._claim_kind_repo,
            payment_repo=self._payment_repo,
            grouped_claim_repo=self._grouped_claim_repo,
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
    def sos_claim_repo(self) -> SosClaimRepoPort:
        return self._sos_claim_repo

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
    def agent_repo(self):
        return self._agent_repo

    @property
    def payment_via_repo(self):
        return self._payment_via_repo

    @property
    def claim_kind_repo(self) -> ClaimKindRepoPort:
        return self._claim_kind_repo

    @property
    def group_claim_repo(self) -> GroupClaimRepoPort:
        return self._group_claim_repo

    @property
    def document_repo(self) -> DocumentRepoPort:
        return self._document_repo

    @property
    def subir_documento(self) -> SubirDocumento:
        return self._subir_documento

    @property
    def descargar_documento(self) -> DescargarDocumento:
        return self._descargar_documento

    @property
    def obtener_documentos(self) -> ObtenerDocumentos:
        return self._obtener_documentos

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
    def registrar_grupo(self) -> RegistrarGrupo:
        return self._registrar_grupo

    @property
    def obtener_grupos(self) -> ObtenerGrupos:
        return self._obtener_grupos

    @property
    def obtener_claim_kinds(self) -> ObtenerClaimKinds:
        return self._obtener_claim_kinds

    @property
    def registrar_gestion_sos(self) -> RegistrarGestionSOS:
        return self._registrar_gestion_sos

    @property
    def registrar_grouped_claim(self) -> RegistrarGroupedClaim:
        return self._registrar_grouped_claim

    @property
    def eliminar_grouped_claim(self) -> EliminarGroupedClaim:
        return self._eliminar_grouped_claim

    @property
    def grouped_claim_repo(self) -> GroupedClaimRepoPort:
        return self._grouped_claim_repo

    @property
    def eliminar_grupo(self) -> EliminarGrupo:
        return self._eliminar_grupo

    @property
    def actualizar_grupo(self) -> ActualizarGrupo:
        return self._actualizar_grupo

    @property
    def actualizar_grupo_de_gestion(self) -> ActualizarGrupoDeGestion:
        return self._actualizar_grupo_de_gestion

    @property
    def registrar_factura(self) -> RegistrarFactura:
        return self._registrar_factura

    @property
    def obtener_facturas(self) -> ObtenerFacturas:
        return self._obtener_facturas

    @property
    def obtener_factura(self) -> ObtenerFactura:
        return self._obtener_factura

    @property
    def eliminar_factura(self) -> EliminarFactura:
        return self._eliminar_factura

    @property
    def obtener_total_facturacion(self) -> ObtenerTotalFacturacion:
        return self._obtener_total_facturacion

    @property
    def crear_periodo(self) -> CrearPeriodo:
        return self._crear_periodo

    @property
    def listar_periodos(self) -> ListarPeriodos:
        return self._listar_periodos

    @property
    def eliminar_periodo(self) -> EliminarPeriodo:
        return self._eliminar_periodo

    @property
    def importar_gestiones_sos(self) -> ImportarGestionSOS:
        return self._importar_gestiones_sos

    @property
    def eliminar_gestion_sos(self) -> EliminarGestionSOS:
        return self._eliminar_gestion_sos

    @property
    def obtener_gestiones(self) -> ObtenerGestiones:
        return self._obtener_gestiones

    @property
    def obtener_gestion_por_id(self) -> ObtenerGestionPorId:
        return self._obtener_gestion_por_id

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
    def auth_router(self) -> AuthRouter:
        return self._auth_router


def get_container() -> Container:
    return Container.get_instance()
