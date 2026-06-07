"""Unit tests for auth use cases using in-memory fakes."""

import pytest

from src.adapters.persistence.inmemory_user_repository import InMemoryUserRepository
from src.application.use_cases.auth import (
    Login,
    LoginInput,
    Logout,
    LogoutInput,
    Me,
    Register,
    RegisterInput,
)


# ── Fakes ────────────────────────────────────────────────────────────────────


class FakePasswordPort:
    def verify_password(self, plain: str, hashed: str) -> bool:
        return plain == hashed  # trivial fake: hash == plain

    def hash_password(self, plain: str) -> str:
        return plain  # trivial fake


class FakeTokenPort:
    def __init__(self):
        self._tokens: dict[str, str] = {}
        self._blacklist: set[str] = set()

    def create_token(self, user_id) -> str:
        token = f"token-{user_id}"
        self._tokens[token] = str(user_id)
        return token

    def verify_token(self, token: str):
        if token in self._blacklist:
            return None
        user_id = self._tokens.get(token)
        if user_id is None:
            return None
        from uuid import UUID

        return UUID(user_id)

    def invalidate_token(self, token: str) -> None:
        self._blacklist.add(token)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def user_repo():
    return InMemoryUserRepository()


@pytest.fixture
def password_port():
    return FakePasswordPort()


@pytest.fixture
def token_port():
    return FakeTokenPort()


# ── Register ─────────────────────────────────────────────────────────────────


def test_register_creates_user(user_repo, password_port):
    use_case = Register(user_repo, password_port)
    result = use_case.execute(
        RegisterInput(user_name="alice", email="alice@example.com", password="secret")
    )

    assert result.user_name == "alice"
    assert result.user_email == "alice@example.com"
    assert result.user_id is not None


def test_register_duplicate_email_raises(user_repo, password_port):
    use_case = Register(user_repo, password_port)
    use_case.execute(
        RegisterInput(user_name="alice", email="alice@example.com", password="s")
    )

    with pytest.raises(ValueError, match="Email already registered"):
        use_case.execute(
            RegisterInput(user_name="alice2", email="alice@example.com", password="s")
        )


# ── Login ─────────────────────────────────────────────────────────────────────


def test_login_returns_token(user_repo, password_port, token_port):
    Register(user_repo, password_port).execute(
        RegisterInput(user_name="alice", email="alice@example.com", password="secret")
    )
    result = Login(user_repo, password_port, token_port).execute(
        LoginInput(email="alice@example.com", password="secret")
    )

    assert result.token.startswith("token-")
    assert result.user_email == "alice@example.com"


def test_login_wrong_password_raises(user_repo, password_port, token_port):
    Register(user_repo, password_port).execute(
        RegisterInput(user_name="alice", email="alice@example.com", password="secret")
    )

    with pytest.raises(ValueError, match="Invalid credentials"):
        Login(user_repo, password_port, token_port).execute(
            LoginInput(email="alice@example.com", password="wrong")
        )


def test_login_unknown_email_raises(user_repo, password_port, token_port):
    with pytest.raises(ValueError, match="Invalid credentials"):
        Login(user_repo, password_port, token_port).execute(
            LoginInput(email="nobody@example.com", password="x")
        )


# ── Me ────────────────────────────────────────────────────────────────────────


def test_me_returns_user_info(user_repo, password_port, token_port):
    reg = Register(user_repo, password_port).execute(
        RegisterInput(user_name="bob", email="bob@example.com", password="pw")
    )
    login = Login(user_repo, password_port, token_port).execute(
        LoginInput(email="bob@example.com", password="pw")
    )
    user_id = token_port.verify_token(login.token)
    result = Me(user_repo).execute(user_id)

    assert result.user_name == "bob"
    assert result.active is True


# ── Logout ────────────────────────────────────────────────────────────────────


def test_logout_invalidates_token(user_repo, password_port, token_port):
    Register(user_repo, password_port).execute(
        RegisterInput(user_name="carol", email="carol@example.com", password="pw")
    )
    login = Login(user_repo, password_port, token_port).execute(
        LoginInput(email="carol@example.com", password="pw")
    )
    token = login.token

    result = Logout(token_port).execute(LogoutInput(token=token))
    assert result.success is True
    assert token_port.verify_token(token) is None


# ── Repository isolation ──────────────────────────────────────────────────────


def test_inmemory_repo_instances_are_isolated():
    repo1 = InMemoryUserRepository()
    repo2 = InMemoryUserRepository()
    repo1.add_user("user1", "u1@example.com", "hash1")

    assert repo2.get_all() == []
