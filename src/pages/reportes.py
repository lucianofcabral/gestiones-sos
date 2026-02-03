"""Página de reportes"""

from nicegui import ui
from src.components.navbar import crear_navbar


@ui.page("/reportes")
def page_reportes():
    """Página de reportes"""
    ui.colors(
        primary="#dc2656", secondary="#ea580c", accent="#fbbf24"
    )
    dark = ui.dark_mode(value=True)
    crear_navbar(dark)

    with ui.column().classes(
        "w-full max-w-7xl mx-auto p-4 gap-4"
    ):
        ui.label("📊 Reportes y Estadísticas").classes("text-h4")

        with ui.card().classes("w-full p-8 text-center"):
            ui.icon("analytics", size="4rem").classes(
                "text-primary"
            )
            ui.label("Módulo de Reportes").classes(
                "text-h5 q-mt-md"
            )
            ui.label(
                "Aquí podrás ver estadísticas y reportes de las gestiones"
            ).classes("text-gray-500")
            ui.label("Próximamente...").classes(
                "text-caption text-gray-400 q-mt-lg"
            )
