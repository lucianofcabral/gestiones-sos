import os

from nicegui import ui

from src.infrastructure.container import get_container
from src.ui.pages.home import register_home_page
from src.ui.pages.login import register_login_page
from src.ui.pages.register import register_register_page
from src.ui.routes.auth import create_auth_routes

container = get_container()
create_auth_routes(container.auth_router)

register_login_page()
register_register_page()
register_home_page()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="Gestiones SOS",
        port=8080,
        reload=False,
        storage_secret=os.environ.get(
            "STORAGE_SECRET", os.environ.get("JWT_SECRET", "")
        ),
    )
