from abc import ABC, abstractmethod

from src.domain.ports.repositories import (
    ClaimRepoPort,
    GroupedClaimRepoPort,
    SosClaimRepoPort,
)


class UnitOfWork(ABC):
    claims: ClaimRepoPort
    sos_claims: SosClaimRepoPort
    grouped_claims: GroupedClaimRepoPort

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
