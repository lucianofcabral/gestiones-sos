"""Placeholder page for new gestion form."""

from nicegui import ui

from src.ui.components.shell import AppShell


def register_gestiones_nueva_page() -> None:
    @ui.page("/gestiones/nueva")
    def gestiones_nueva_page() -> None:
        with AppShell():
            ui.label("Nueva Gestión").classes("text-2xl font-bold")
            ui.label("Próximamente — formulario de nueva gestión.").classes(
                "text-gray-400 mt-2"
            )
