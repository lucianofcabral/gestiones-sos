"""Página de gestión de clientes"""

from nicegui import ui
from src.components.navbar import crear_navbar


@ui.page("/clientes")
def page_clientes():
    """Página de clientes"""
    ui.colors(
        primary="#dc2656", secondary="#ea580c", accent="#fbbf24"
    )
    dark = ui.dark_mode(value=True)
    crear_navbar(dark)

    with ui.column().classes(
        "w-full max-w-7xl mx-auto p-4 gap-4"
    ):
        ui.label("👥 Gestión de Clientes").classes("text-h4")

        with ui.card().classes("w-full p-8 text-center"):
            ui.icon("people", size="4rem").classes("text-primary")
            ui.label("Módulo de Clientes").classes(
                "text-h5 q-mt-md"
            )
            ui.label(
                "Aquí podrás gestionar la información de los clientes"
            ).classes("text-gray-500")
            ui.label("Próximamente...").classes(
                "text-caption text-gray-400 q-mt-lg"
            )
