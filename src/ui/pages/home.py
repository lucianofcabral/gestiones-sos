"""Home page — metrics dashboard with total claims, recent claims, and stat cards."""

from nicegui import ui

from src.domain.models.entities import Claim, Payment
from src.infrastructure.container import Container
from src.ui.components.shell import AppShell


def register_home_page() -> None:
    @ui.page("/")
    def home_page() -> None:
        with AppShell():
            container = Container.get_instance()

            claims = container.claim_repo.get_all()
            payments = container.payment_repo.get_all()
            periods = container.period_repo.get_n_last(1)

            _render_metrics(claims, payments, periods)


def _render_metrics(
    claims: list[Claim],
    payments: list[Payment],
    periods: list,
) -> None:
    with ui.column().classes("p-8 w-full max-w-5xl mx-auto gap-8"):
        # ── Total claims counter ───────────────────────────────────────────────
        with ui.card().classes("w-full p-6"):
            ui.label("Total Siniestros").classes(
                "text-sm text-gray-400 uppercase tracking-wide"
            )
            ui.label(str(len(claims))).classes("text-4xl font-bold")

        # ── Recent 5 claims ────────────────────────────────────────────────────
        ui.label("Últimos Siniestros").classes("text-lg font-semibold")

        sorted_claims = sorted(claims, key=lambda c: c.created_at, reverse=True)[:5]

        if sorted_claims:
            columns = [
                {
                    "name": "claimer",
                    "label": "Reclamante",
                    "field": "claimer",
                    "align": "left",
                },
                {
                    "name": "policy",
                    "label": "Póliza",
                    "field": "policy",
                    "align": "left",
                },
                {
                    "name": "plate",
                    "label": "Patente",
                    "field": "plate",
                    "align": "left",
                },
                {"name": "date", "label": "Fecha", "field": "date", "align": "left"},
            ]
            rows = [
                {
                    "claimer": c.claimer_name,
                    "policy": c.policy_number,
                    "plate": c.plate,
                    "date": c.created_at.strftime("%d/%m/%Y"),
                }
                for c in sorted_claims
            ]
            ui.table(columns=columns, rows=rows, row_key="claimer").classes("w-full")
        else:
            ui.label("No hay siniestros registrados.").classes("text-gray-400 italic")

        # ── Stat cards ─────────────────────────────────────────────────────────
        pending_sos = sum(1 for c in claims if not c.solved)
        active_payments = sum(1 for p in payments if p.active)
        current_period = periods[0].period_name if periods else "—"

        with ui.row().classes("gap-4 w-full"):
            _stat_card("Pendientes SOS", str(pending_sos), "warning")
            _stat_card("Pagos Activos", str(active_payments), "payments")
            _stat_card("Período Actual", current_period, "calendar_month")


def _stat_card(title: str, value: str, icon_name: str) -> None:
    with ui.card().classes("flex-1 min-w-40 p-4"):
        with ui.row().classes("items-center gap-3"):
            ui.icon(icon_name, size="2rem")
            with ui.column().classes("gap-0"):
                ui.label(title).classes("text-xs text-gray-400 uppercase tracking-wide")
                ui.label(value).classes("text-2xl font-bold")
