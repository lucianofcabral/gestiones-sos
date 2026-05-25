from typing import Any
from uuid import UUID

from src.domain.models.entities import User


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._store: list[User] = []

    def add(self, model: User) -> User:
        self._store.append(model)
        return model

    def get_by_id(self, id: UUID) -> User | None:
        for user in self._store:
            if user.user_id == id:
                return user
        return None

    def delete(self, id: UUID) -> None:
        self._store = [u for u in self._store if u.user_id != id]

    def update(self, id: UUID, model: User) -> bool:
        for i, user in enumerate(self._store):
            if user.user_id == id:
                self._store[i] = model
                return True
        return False

    def get_all(self) -> list[User]:
        return list(self._store)

    def exists(self, data: dict[str, Any]) -> bool:
        return any(
            all(getattr(u, k) == v for k, v in data.items())
            for u in self._store
        )

    def get_by_ids(self, ids: list[UUID]) -> list[User]:
        return [u for u in self._store if u.user_id in ids]

    def get_by_email(self, email: str) -> User | None:
        for user in self._store:
            if user.user_email == email:
                return user
        return None

    def get_by_name(self, name: str) -> User | None:
        for user in self._store:
            if user.user_name == name:
                return user
        return None

    def add_user(self, user_name: str, email: str, password_hash: str) -> User:
        new_user = User(
            user_name=user_name,
            user_email=email,
            password_hash=password_hash,
        )
        return self.add(new_user)

    def activate(self, id: UUID) -> bool:
        user = self.get_by_id(id)
        if user:
            return self.update(id, user.model_copy(update={"active": True}))
        return False

    def inactivate(self, id: UUID) -> bool:
        user = self.get_by_id(id)
        if user:
            return self.update(id, user.model_copy(update={"active": False}))
        return False