from abc import ABC, abstractmethod

from src.domain.ports.repositories import ClaimRepoPort, SosClaimRepoPort


class UnitOfWork(ABC):
    claims: ClaimRepoPort
    sos_claims: SosClaimRepoPort

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
