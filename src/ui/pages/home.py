from nicegui import app, ui

from src.ui.components.navbar import crear_navbar


def register_home_page() -> None:
    @ui.page("/")
    def home_page() -> None:
        if not app.storage.user.get("token"):
            ui.navigate.to("/login")
            return

        crear_navbar()

        with ui.column().classes("p-8 w-full max-w-4xl mx-auto gap-6"):
            with ui.row().classes("items-center gap-2"):
                ui.label(
                    f"Bienvenido, {app.storage.user.get('user_name', '')} 👋"
                ).classes("text-2xl font-bold text-blue-800")

            ui.separator()

            ui.label("Módulos disponibles").classes("text-lg font-semibold text-gray-600")

            with ui.row().classes("gap-4 flex-wrap"):
                _module_card("Gestiones", "assignment", "Siniestros y gestiones", "blue", "/gestiones")
                _module_card("Pagos", "payments", "Control de pagos", "green", "/pagos")
                _module_card("Períodos", "calendar_month", "Gestión de períodos", "orange", "/periodos")
                _module_card("Reportes", "bar_chart", "Estadísticas y análisis", "purple", "/reportes")


def _module_card(title: str, icon: str, subtitle: str, color: str, path: str) -> None:
    with ui.card().classes(
        f"w-44 h-44 cursor-pointer shadow-md hover:shadow-xl transition-shadow rounded-xl items-center justify-center gap-2"
    ).on("click", lambda p=path: ui.navigate.to(p)):
        ui.icon(icon, size="2.5rem", color=f"{color}-7")
        ui.label(title).classes("text-base font-bold text-gray-800")
        ui.label(subtitle).classes("text-xs text-gray-500 text-center")
