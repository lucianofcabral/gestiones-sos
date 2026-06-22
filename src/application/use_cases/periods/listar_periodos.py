"""ListarPeriodos — list all Periods ordered by recency."""

from pydantic import BaseModel

from src.domain.models.entities import Period
from src.domain.ports.repositories import PeriodRepoPort


class ListarPeriodos:
    """Return all periods ordered by year DESC, month DESC."""

    class Output(BaseModel):
        periods: list[Period]

    def __init__(self, period_repo: PeriodRepoPort) -> None:
        self._period_repo = period_repo

    def execute(self) -> Output:
        return self.Output(periods=self._period_repo.get_n_last(None))
