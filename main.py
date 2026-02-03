"""
Punto de entrada principal de la aplicación Gestiones SOS
"""

from nicegui import ui
from src.config import APP_TITLE, APP_PORT

# Importar páginas (esto registra automáticamente las rutas)
import src.pages

# Iniciar aplicación
ui.run(
    title=APP_TITLE,
    port=APP_PORT,
    reload=True,
    show=True,
    dark=True,
)
