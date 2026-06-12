"""Catalogos page — read-only view of agents, payment vias, and claim kinds."""

from nicegui import ui

from src.infrastructure.container import Container
from src.ui.components.shell import AppShell


def register_catalogos_page() -> None:
    @ui.page("/catalogos")
    def catalogos_page() -> None:
        with AppShell():
            container = Container.get_instance()

            ui.label("Catálogos").classes("text-2xl font-bold")

            with ui.tabs().classes("mt-4") as tabs:
                ui.tab("Agentes", icon="people")
                ui.tab("Medios de Pago", icon="payments")
                ui.tab("Tipos de Siniestro", icon="category")

            with ui.tab_panels(tabs, value="Agentes").classes("w-full"):
                with ui.tab_panel("Agentes"):
                    agents = container.agent_repo.get_all()
                    _render_agent_table(agents)

                with ui.tab_panel("Medios de Pago"):
                    payment_vias = container.payment_via_repo.get_all()
                    _render_payment_via_table(payment_vias)

                with ui.tab_panel("Tipos de Siniestro"):
                    claim_kinds = container.claim_kind_repo.get_all()
                    _render_claim_kind_table(claim_kinds)


def _render_agent_table(agents: list) -> None:
    columns = [
        {"name": "name", "label": "Nombre", "field": "name", "align": "left"},
        {"name": "active", "label": "Activo", "field": "active", "align": "center"},
    ]
    rows = [
        {
            "name": a.name,
            "active": "Sí" if a.active else "No",
        }
        for a in agents
    ]
    ui.table(columns=columns, rows=rows, row_key="name").classes("w-full mt-2")


def _render_payment_via_table(payment_vias: list) -> None:
    columns = [
        {"name": "name", "label": "Nombre", "field": "name", "align": "left"},
        {"name": "active", "label": "Activo", "field": "active", "align": "center"},
    ]
    rows = [
        {
            "name": p.name,
            "active": "Sí" if p.active else "No",
        }
        for p in payment_vias
    ]
    ui.table(columns=columns, rows=rows, row_key="name").classes("w-full mt-2")


def _render_claim_kind_table(claim_kinds: list) -> None:
    columns = [
        {"name": "name", "label": "Nombre", "field": "name", "align": "left"},
        {"name": "active", "label": "Activo", "field": "active", "align": "center"},
    ]
    rows = [
        {
            "name": c.name,
            "active": "Sí" if c.active else "No",
        }
        for c in claim_kinds
    ]
    ui.table(columns=columns, rows=rows, row_key="name").classes("w-full mt-2")
