from nicegui import app

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
            raise ValueError("Invalid token")
        return self._me_use_case.execute(user_id)

    def logout(self, token: str) -> LogoutOutput:
        return self._logout_use_case.execute(LogoutInput(token=token))


def create_auth_routes(auth_router: AuthRouter):
    @app.post("/api/auth/login")
    async def api_login(body: dict):
        try:
            result = auth_router.login(body["email"], body["password"])
            return {
                "success": True,
                "data": {
                    "token": result.token,
                    "user_id": result.user_id,
                    "user_name": result.user_name,
                    "user_email": result.user_email,
                },
            }
        except KeyError as e:
            return {"success": False, "error": f"Missing field: {e}"}
        except ValueError as e:
            return {"success": False, "error": str(e)}

    @app.post("/api/auth/register")
    async def api_register(body: dict):
        try:
            result = auth_router.register(
                body["user_name"], body["email"], body["password"]
            )
            return {
                "success": True,
                "data": {
                    "user_id": result.user_id,
                    "user_name": result.user_name,
                    "user_email": result.user_email,
                },
            }
        except KeyError as e:
            return {"success": False, "error": f"Missing field: {e}"}
        except ValueError as e:
            return {"success": False, "error": str(e)}

    @app.get("/api/auth/me")
    async def api_me(token: str):
        try:
            result = auth_router.me(token)
            return {
                "success": True,
                "data": {
                    "user_id": result.user_id,
                    "user_name": result.user_name,
                    "user_email": result.user_email,
                    "active": result.active,
                },
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}

    @app.post("/api/auth/logout")
    async def api_logout(body: dict):
        try:
            result = auth_router.logout(body["token"])
            return {"success": result.success, "message": result.message}
        except KeyError as e:
            return {"success": False, "error": f"Missing field: {e}"}
