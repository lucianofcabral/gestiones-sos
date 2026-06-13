"""CrearPeriodo — create a new Period with duplicate (year, month) guard."""

from pydantic import BaseModel, Field

from src.domain.models.entities import Period, _MESES_ES
from src.domain.ports.repositories import PeriodRepoPort


class CrearPeriodo:
    """Create a new Period.

    Raises ValueError if a Period with the same (year, month) already exists.
    """

    class Input(BaseModel):
        year: int = Field(ge=2020, lt=2040)
        month: int = Field(ge=1, le=12)

    class Output(BaseModel):
        period: Period

    def __init__(self, period_repo: PeriodRepoPort) -> None:
        self._period_repo = period_repo

    def execute(self, input: Input) -> Output:
        if self._period_repo.get_by_year_month(input.year, input.month):
            raise ValueError(
                f"Ya existe un período para {_MESES_ES[input.month].capitalize()} {input.year}"
            )
        period = Period(year=input.year, month=input.month)
        created = self._period_repo.add(period)
        return self.Output(period=created)
