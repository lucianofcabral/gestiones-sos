import os

from src.adapters.auth import JwtService, PasswordAdapter
from src.adapters.persistence.sqlalchemy_claim_repository import (
    SqlAlchemyClaimRepository,
)
from src.adapters.persistence.sqlalchemy_period_repository import (
    SqlAlchemyPeriodRepository,
)
from src.adapters.persistence.sqlalchemy_user_repository import SqlAlchemyUserRepository
from src.application.use_cases.claims.eliminar_gestion_sos import EliminarGestionSOS
from src.domain.ports.repositories import ClaimRepoPort, PeriodRepoPort, UserRepoPort
from src.ui.routes.auth import AuthRouter


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


class Container:
    _instance: "Container | None" = None

    def __init__(self):
        jwt_secret = os.environ.get("JWT_SECRET")
        if not jwt_secret:
            raise RuntimeError("JWT_SECRET environment variable is not set")

        self._user_repo = _build_user_repo()
        self._claim_repo = _build_claim_repo()
        self._period_repo = _build_period_repo()
        self._password_adapter = PasswordAdapter()
        self._jwt_service = JwtService(secret=jwt_secret)
        self._eliminar_gestion_sos = EliminarGestionSOS(claim_repo=self._claim_repo)
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
    def password_adapter(self) -> PasswordAdapter:
        return self._password_adapter

    @property
    def jwt_service(self) -> JwtService:
        return self._jwt_service

    @property
    def eliminar_gestion_sos(self) -> EliminarGestionSOS:
        return self._eliminar_gestion_sos

    @property
    def auth_router(self) -> AuthRouter:
        return self._auth_router


def get_container() -> Container:
    return Container.get_instance()
