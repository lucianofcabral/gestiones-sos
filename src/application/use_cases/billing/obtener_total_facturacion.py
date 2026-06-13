"""ObtenerTotalFacturacion — calculate total billing for a given year/month."""

from src.domain.ports.repositories import PeriodRepoPort


class ObtenerTotalFacturacion:
    """Return the sum of all Invoice amounts for the given year and month."""

    def __init__(self, period_repo: PeriodRepoPort) -> None:
        self._period_repo = period_repo

    def execute(self, year: int, month: int) -> float:
        return self._period_repo.get_total_billing_by_year_month(year, month)
