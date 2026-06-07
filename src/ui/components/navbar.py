from nicegui import app, ui


def crear_navbar(titulo: str = "Gestiones SOS") -> None:
    """Top navigation bar with title and logout button."""
    with ui.header().classes(
        "bg-blue-700 text-white items-center justify-between px-6 py-3"
    ):
        with ui.row().classes("items-center gap-3"):
            ui.icon("local_police", size="1.6rem")
            ui.label(titulo).classes("text-xl font-semibold tracking-wide")

        token = app.storage.user.get("token")
        if token:
            with ui.row().classes("items-center gap-2"):
                user_name = app.storage.user.get("user_name", "")
                if user_name:
                    ui.label(f"👤 {user_name}").classes("text-sm opacity-90")
                ui.button(
                    "Salir",
                    icon="logout",
                    on_click=_logout,
                ).props("flat color=white").classes("text-sm")


async def _logout() -> None:
    app.storage.user.clear()
    ui.navigate.to("/login")
