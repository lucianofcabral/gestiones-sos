from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from src.domain.ports.auth import TokenPort

ALGORITHM = "HS256"


class JwtService:
    def __init__(self, secret: str, expire_minutes: int = 60):
        self._secret = secret
        self._expire_minutes = expire_minutes
        self._blacklist: set[str] = set()

    def create_token(self, user_id: UUID) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self._expire_minutes)
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, self._secret, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> UUID | None:
        if token in self._blacklist:
            return None
        try:
            payload = jwt.decode(token, self._secret, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                return None
            return UUID(user_id)
        except jwt.InvalidTokenError:
            return None

    def invalidate_token(self, token: str) -> None:
        try:
            jwt.decode(token, self._secret, algorithms=[ALGORITHM])
            self._blacklist.add(token)
        except jwt.ExpiredSignatureError:
            pass  # Already expired — no need to blacklist
        except jwt.InvalidTokenError:
            pass  # Invalid token — nothing to invalidate

    def _purge_expired(self) -> None:
        """Remove expired tokens from the blacklist to prevent unbounded growth."""
        valid = set()
        for token in self._blacklist:
            try:
                jwt.decode(token, self._secret, algorithms=[ALGORITHM])
                valid.add(token)
            except jwt.ExpiredSignatureError:
                pass  # Drop it
            except jwt.InvalidTokenError:
                pass
        self._blacklist = valid


# Structural subtype check
_: TokenPort = JwtService(secret="")  # type: ignore[assignment]
