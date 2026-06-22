"""Periodos page — create, list, and delete Periods."""

from nicegui import ui

from src.domain.models.entities import Period
from src.infrastructure.container import Container
from src.ui.components.shell import AppShell

_MESES_ES = [
    "",
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]


def register_periodos_page() -> None:
    @ui.page("/periodos")
    def periodos_page() -> None:
        with AppShell():
            container = Container.get_instance()

            ui.label("Períodos").classes("text-2xl font-bold")

            # ── Create form ──────────────────────────────────────────────────
            with ui.card().classes("w-full max-w-md mt-4 p-4"):
                ui.label("Nuevo Período").classes("text-lg font-bold")

                year_input = ui.number(
                    label="Año",
                    min=2020,
                    max=2039,
                    precision=0,
                ).classes("w-full")
                month_select = ui.select(
                    label="Mes",
                    options={m: _MESES_ES[m].capitalize() for m in range(1, 13)},
                ).classes("w-full")

                async def _create_period() -> None:
                    year = year_input.value
                    month = month_select.value

                    if not year or not month:
                        ui.notify("Debe completar año y mes", type="warning")
                        return

                    try:
                        inp = container.crear_periodo.Input(
                            year=int(year), month=int(month)
                        )
                        container.crear_periodo.execute(inp)
                        ui.notify("Período creado", type="positive")
                        year_input.value = None
                        month_select.value = None
                        _render_periods.refresh()
                    except ValueError as e:
                        ui.notify(str(e), type="negative")
                    except Exception as e:
                        ui.notify(f"Error: {e}", type="negative")

                ui.button(
                    "Crear",
                    icon="add",
                    on_click=_create_period,
                )

            # ── Period list ──────────────────────────────────────────────────

            @ui.refreshable
            def _render_periods() -> None:
                periods = container.listar_periodos.execute().periods

                if not periods:
                    ui.label("No hay períodos registrados.").classes(
                        "text-gray-400 mt-4"
                    )
                    return

                for period in periods:
                    with ui.row().classes("items-center gap-4 py-1"):
                        ui.label(period.period_name).classes("text-sm w-40")
                        ui.label(str(period.period_number)).classes(
                            "text-sm w-28 text-gray-400"
                        )
                        ui.label(period.created_at.strftime("%Y-%m-%d %H:%M")).classes(
                            "text-sm w-36 text-gray-400"
                        )
                        _delete_button(period, _render_periods)

            def _confirm_delete(period: Period, refresh_fn) -> None:
                def _do_delete() -> None:
                    try:
                        inp = container.eliminar_periodo.Input(
                            period_id=period.period_id
                        )
                        result = container.eliminar_periodo.execute(inp)
                        if result.deleted:
                            ui.notify("Período eliminado", type="positive")
                            refresh_fn.refresh()
                    except ValueError as e:
                        ui.notify(str(e), type="negative")
                    except Exception as e:
                        ui.notify(f"Error: {e}", type="negative")

                _do_delete()

            def _delete_button(period: Period, refresh_fn) -> ui.button:
                return ui.button(
                    "Eliminar",
                    icon="delete",
                    on_click=lambda p=period: _confirm_delete(p, refresh_fn),
                ).props("flat size=sm")

            # ── Initial render ───────────────────────────────────────────────
            _render_periods()
