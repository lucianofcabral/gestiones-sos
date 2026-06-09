"""Placeholder page for periodos list view."""

from nicegui import ui

from src.ui.components.shell import AppShell


def register_periodos_page() -> None:
    @ui.page("/periodos")
    def periodos_page() -> None:
        with AppShell():
            ui.label("Períodos").classes("text-2xl font-bold")
            ui.label("Próximamente — gestión de períodos.").classes(
                "text-gray-400 mt-2"
            )
