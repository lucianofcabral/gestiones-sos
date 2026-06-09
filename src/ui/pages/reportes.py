"""Placeholder page for reportes view."""

from nicegui import ui

from src.ui.components.shell import AppShell


def register_reportes_page() -> None:
    @ui.page("/reportes")
    def reportes_page() -> None:
        with AppShell():
            ui.label("Reportes").classes("text-2xl font-bold")
            ui.label("Próximamente — estadísticas y análisis.").classes(
                "text-gray-400 mt-2"
            )
