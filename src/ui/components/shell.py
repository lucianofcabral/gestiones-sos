"""AppShell context manager — dark-themed layout with auth guard, header, and sidebar."""

from nicegui import app, ui


class AppShell:
    """Context manager wrapping every authenticated page with shared layout.

    On entry:
    1. Check auth — redirects to /login if no token
    2. Enable dark mode
    3. Render header with title + user info + logout
    4. Render sidebar with nav items (left_drawer, fallback ui.row)

    Usage inside a @ui.page function::

        with AppShell():
            ui.label("Page content")
    """

    def __init__(self, title: str = "Gestiones SOS") -> None:
        self._title = title

    def __enter__(self) -> None:
        if "token" not in app.storage.user:
            ui.navigate.to("/login")
            return

        ui.dark_mode().enable()

        self._render_header()
        self._render_sidebar()

    def __exit__(self, *args: object) -> None:
        pass

    def _render_header(self) -> None:
        with ui.header().classes("items-center justify-between px-6 py-3"):
            with ui.row().classes("items-center gap-3"):
                ui.icon("local_police", size="1.6rem")
                ui.label(self._title).classes("text-xl font-semibold tracking-wide")

            user_name = app.storage.user.get("user_name", "")
            if user_name:
                with ui.row().classes("items-center gap-2"):
                    ui.label(user_name).classes("text-sm opacity-90")
                    ui.button(
                        "Salir",
                        icon="logout",
                        on_click=self._logout,
                    ).props("flat color=white").classes("text-sm")

    def _render_sidebar(self) -> None:
        try:
            with ui.left_drawer().classes("bg-gray-900"):
                self._render_nav_items()
        except Exception:
            with ui.row().classes("w-48 bg-gray-900 min-h-screen"):
                self._render_nav_items()

    def _render_nav_items(self) -> None:
        with ui.column().classes("w-full gap-1 p-4"):
            for label, target, icon_name in self._nav_items():
                self._nav_item(label, target, icon_name)

    def _nav_item(self, label: str, target: str, icon_name: str) -> None:
        with ui.link(target=target).classes("no-underline"):
            with ui.row().classes(
                "items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-700"
            ):
                ui.icon(icon_name, size="1.2rem")
                ui.label(label).classes("text-sm")

    @staticmethod
    def _nav_items() -> list[tuple[str, str, str]]:
        return [
            ("Inicio", "/", "home"),
            ("Documentos", "/documentos", "description"),
            ("Gestiones", "/gestiones", "assignment"),
            ("Nueva Gestión", "/gestiones/nueva", "add_circle"),
            ("Pagos", "/pagos", "payments"),
            ("Períodos", "/periodos", "calendar_month"),
            ("Grupos", "/grupos", "group"),
            ("Catálogos", "/catalogos", "list"),
            ("Reportes", "/reportes", "bar_chart"),
        ]

    @staticmethod
    async def _logout() -> None:
        app.storage.user.clear()
        ui.navigate.to("/login")
