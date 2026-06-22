from uuid import UUID

from src.application.use_cases.auth.login import LoginInput, LoginOutput
from src.application.use_cases.auth.logout import LogoutInput, LogoutOutput
from src.application.use_cases.auth.me import MeOutput
from src.application.use_cases.auth.register import RegisterInput, RegisterOutput
from src.domain.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    UserInactiveError,
    UserNotFoundError,
)
from src.domain.ports.auth import PasswordPort, TokenPort
from src.domain.ports.repositories import UserRepoPort


class Login:
    def __init__(
        self,
        user_repo: UserRepoPort,
        password_port: PasswordPort,
        token_port: TokenPort,
    ):
        self._user_repo = user_repo
        self._password_port = password_port
        self._token_port = token_port

    def execute(self, input_data: LoginInput) -> LoginOutput:
        user = self._user_repo.get_by_email(input_data.email)
        if user is None:
            raise InvalidCredentialsError("Invalid credentials")

        if not self._password_port.verify_password(
            input_data.password, user.password_hash
        ):
            raise InvalidCredentialsError("Invalid credentials")

        if not user.active:
            raise UserInactiveError("User is inactive")

        token = self._token_port.create_token(user.user_id)
        return LoginOutput(
            token=token,
            user_id=str(user.user_id),
            user_name=user.user_name,
            user_email=str(user.user_email),
        )


class Register:
    def __init__(self, user_repo: UserRepoPort, password_port: PasswordPort):
        self._user_repo = user_repo
        self._password_port = password_port

    def execute(self, input_data: RegisterInput) -> RegisterOutput:
        existing = self._user_repo.get_by_email(input_data.email)
        if existing is not None:
            raise EmailAlreadyRegisteredError("Email already registered")

        password_hash = self._password_port.hash_password(input_data.password)

        new_user = self._user_repo.add_user(
            user_name=input_data.user_name,
            email=str(input_data.email),
            password_hash=password_hash,
        )

        return RegisterOutput(
            user_id=str(new_user.user_id),
            user_name=new_user.user_name,
            user_email=str(new_user.user_email),
        )


class Me:
    def __init__(self, user_repo: UserRepoPort):
        self._user_repo = user_repo

    def execute(self, user_id: UUID) -> MeOutput:
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError("User not found")
        return MeOutput(
            user_id=str(user.user_id),
            user_name=user.user_name,
            user_email=str(user.user_email),
            active=user.active,
        )


class Logout:
    def __init__(self, token_port: TokenPort):
        self._token_port = token_port

    def execute(self, input_data: LogoutInput) -> LogoutOutput:
        self._token_port.invalidate_token(input_data.token)
        return LogoutOutput(success=True, message="Logged out successfully")
