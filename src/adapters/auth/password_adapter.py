from passlib.context import CryptContext

from src.domain.ports.auth import PasswordPort

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordAdapter:
    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    def hash_password(self, plain: str) -> str:
        return pwd_context.hash(plain)


# Structural subtype check
_: PasswordPort = PasswordAdapter()  # type: ignore[assignment]
