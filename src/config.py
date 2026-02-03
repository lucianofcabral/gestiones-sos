from nicegui import ui

APP_TITLE = "Gestiones SOS"
APP_PORT = 8080


def setup_theme():
    """Configura el tema de colores de la aplicación"""
    ui.colors(
        primary="#dc2656", secondary="#ea580c", accent="#fbbf24"
    )
