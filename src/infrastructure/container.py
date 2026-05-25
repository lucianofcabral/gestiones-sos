import os

from src.adapters.auth import JwtService, PasswordAdapter
from src.adapters.persistence.inmemory_user_repository import InMemoryUserRepository
from src.ui.routes.auth import AuthRouter


class Container:
    _instance: "Container | None" = None

    def __init__(self):
        jwt_secret = os.environ.get("JWT_SECRET")
        if not jwt_secret:
            raise RuntimeError("JWT_SECRET environment variable is not set")

        self._user_repo = InMemoryUserRepository()
        self._password_adapter = PasswordAdapter()
        self._jwt_service = JwtService(secret=jwt_secret)
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
    def user_repo(self):
        return self._user_repo

    @property
    def password_adapter(self):
        return self._password_adapter

    @property
    def jwt_service(self):
        return self._jwt_service

    @property
    def auth_router(self):
        return self._auth_router


def get_container() -> Container:
    return Container.get_instance()