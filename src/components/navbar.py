"""Componente de navegación principal"""

from nicegui import ui


def crear_navbar(dark_mode):
    """Crea el header con navegación y controles"""
    with ui.header().classes("items-center justify-between px-6"):
        # Logo/Título
        ui.label("🆘 Control de Gestiones SOS").classes(
            "text-h5 font-bold cursor-pointer"
        ).on("click", lambda: ui.navigate.to("/"))

        # Navegación central
        with ui.row().classes("gap-1"):
            ui.button(
                "Gestiones",
                on_click=lambda: ui.navigate.to("/"),
            ).props("flat color=white")
            ui.button(
                "Pagos",
                on_click=lambda: ui.navigate.to("/pagos"),
            ).props("flat color=white")
            ui.button(
                "Clientes",
                on_click=lambda: ui.navigate.to("/clientes"),
            ).props("flat color=white")
            ui.button(
                "Reportes",
                on_click=lambda: ui.navigate.to("/reportes"),
            ).props("flat color=white")

        # Botón de tema
        ui.button(
            icon="dark_mode"
            if not dark_mode.value
            else "light_mode",
            on_click=lambda: dark_mode.set_value(
                not dark_mode.value
            ),
        ).props("flat round color=white")
