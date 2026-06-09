"""Placeholder page for gestion detail view (dynamic route)."""

from nicegui import ui

from src.ui.components.shell import AppShell


def register_gestiones_detalle_page() -> None:
    @ui.page("/gestiones/{id}")
    def gestiones_detalle_page(id: str) -> None:
        with AppShell():
            ui.label("Detalle de Gestión").classes("text-2xl font-bold")
            ui.label(f"Gestión ID: {id}").classes("text-gray-400 mt-2")
            ui.label("Próximamente — detalle completo de la gestión.").classes(
                "text-gray-400"
            )
