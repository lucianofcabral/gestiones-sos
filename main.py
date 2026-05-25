from nicegui import ui

from src.infrastructure.container import get_container
from src.ui.routes.auth import create_auth_routes

container = get_container()
create_auth_routes(container.auth_router)


@ui.page("/")
def main():
    ui.label("Gestiones SOS")
    ui.markdown("## Welcome to Gestiones SOS")
    ui.label("API Authentication endpoints available at /api/auth/*")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Gestiones SOS", port=8080, reload=False)