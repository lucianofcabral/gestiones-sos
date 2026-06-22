import bcrypt

from src.domain.ports.auth import PasswordPort


class PasswordAdapter:
    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    def hash_password(self, plain: str) -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


# Structural subtype check
_: PasswordPort = PasswordAdapter()  # type: ignore[assignment]
