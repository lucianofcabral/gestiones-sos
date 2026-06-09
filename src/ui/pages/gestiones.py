"""Placeholder page for gestiones list view."""

from nicegui import ui

from src.ui.components.shell import AppShell


def register_gestiones_page() -> None:
    @ui.page("/gestiones")
    def gestiones_page() -> None:
        with AppShell():
            ui.label("Gestiones").classes("text-2xl font-bold")
            ui.label("Próximamente — listado de siniestros y gestiones.").classes(
                "text-gray-400 mt-2"
            )
