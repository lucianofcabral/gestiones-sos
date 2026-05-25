from typing import Any
from uuid import UUID

import sqlalchemy as sa

from src.domain.models.entities import User
from src.infrastructure.database.connection import get_connection
from src.infrastructure.database.tables import users


class PostgreSQLUserRepository:
    """Implementación de UserRepoPort usando SQLAlchemy Core + PostgreSQL."""

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_user(row: sa.Row) -> User:
        return User(
            user_id=row.user_id,
            user_name=row.user_name,
            user_email=row.user_email,
            password_hash=row.password_hash,
            active=row.active,
            created_at=row.created_at,
        )

    # ── UserRepoPort ──────────────────────────────────────────────────────────

    def add(self, model: User) -> User:
        with get_connection() as conn:
            conn.execute(
                sa.insert(users).values(
                    user_id=model.user_id,
                    user_name=model.user_name,
                    user_email=str(model.user_email),
                    password_hash=model.password_hash,
                    active=model.active,
                    created_at=model.created_at,
                )
            )
            conn.commit()
        return model

    def get_by_id(self, id: UUID) -> User | None:
        with get_connection() as conn:
            row = conn.execute(
                sa.select(users).where(users.c.user_id == id)
            ).fetchone()
        return self._row_to_user(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        with get_connection() as conn:
            row = conn.execute(
                sa.select(users).where(users.c.user_email == email)
            ).fetchone()
        return self._row_to_user(row) if row else None

    def get_by_name(self, name: str) -> User | None:
        with get_connection() as conn:
            row = conn.execute(
                sa.select(users).where(users.c.user_name == name)
            ).fetchone()
        return self._row_to_user(row) if row else None

    def get_all(self) -> list[User]:
        with get_connection() as conn:
            rows = conn.execute(sa.select(users)).fetchall()
        return [self._row_to_user(r) for r in rows]

    def get_by_ids(self, ids: list[UUID]) -> list[User]:
        with get_connection() as conn:
            rows = conn.execute(
                sa.select(users).where(users.c.user_id.in_(ids))
            ).fetchall()
        return [self._row_to_user(r) for r in rows]

    def exists(self, data: dict[str, Any]) -> bool:
        conditions = [users.c[k] == v for k, v in data.items()]
        with get_connection() as conn:
            row = conn.execute(
                sa.select(users.c.user_id).where(sa.and_(*conditions))
            ).fetchone()
        return row is not None

    def delete(self, id: UUID) -> None:
        with get_connection() as conn:
            conn.execute(sa.delete(users).where(users.c.user_id == id))
            conn.commit()

    def update(self, id: UUID, model: User) -> bool:
        with get_connection() as conn:
            result = conn.execute(
                sa.update(users)
                .where(users.c.user_id == id)
                .values(
                    user_name=model.user_name,
                    user_email=str(model.user_email),
                    password_hash=model.password_hash,
                    active=model.active,
                )
            )
            conn.commit()
        return result.rowcount > 0

    def add_user(self, user_name: str, email: str, password_hash: str) -> User:
        new_user = User(
            user_name=user_name,
            user_email=email,
            password_hash=password_hash,
        )
        return self.add(new_user)

    def activate(self, id: UUID) -> bool:
        with get_connection() as conn:
            result = conn.execute(
                sa.update(users).where(users.c.user_id == id).values(active=True)
            )
            conn.commit()
        return result.rowcount > 0

    def inactivate(self, id: UUID) -> bool:
        with get_connection() as conn:
            result = conn.execute(
                sa.update(users).where(users.c.user_id == id).values(active=False)
            )
            conn.commit()
        return result.rowcount > 0
