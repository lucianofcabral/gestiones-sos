from src.application.use_cases.auth import (
    Login,
    LoginInput,
    LoginOutput,
    Logout,
    LogoutOutput,
    LogoutInput,
    Me,
    MeOutput,
    Register,
    RegisterInput,
    RegisterOutput,
)
from src.domain.exceptions import InvalidTokenError
from src.domain.ports.auth import PasswordPort, TokenPort
from src.domain.ports.repositories import UserRepoPort


class AuthRouter:
    def __init__(
        self,
        user_repo: UserRepoPort,
        password_port: PasswordPort,
        token_port: TokenPort,
    ):
        self._token_port = token_port
        self._login_use_case = Login(user_repo, password_port, token_port)
        self._register_use_case = Register(user_repo, password_port)
        self._me_use_case = Me(user_repo)
        self._logout_use_case = Logout(token_port)

    def login(self, email: str, password: str) -> LoginOutput:
        return self._login_use_case.execute(LoginInput(email=email, password=password))

    def register(self, user_name: str, email: str, password: str) -> RegisterOutput:
        return self._register_use_case.execute(
            RegisterInput(user_name=user_name, email=email, password=password)
        )

    def me(self, token: str) -> MeOutput:
        user_id = self._token_port.verify_token(token)
        if user_id is None:
            raise InvalidTokenError("Invalid token")
        return self._me_use_case.execute(user_id)

    def logout(self, token: str) -> LogoutOutput:
        return self._logout_use_case.execute(LogoutInput(token=token))
