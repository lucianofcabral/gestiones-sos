import os

from nicegui import ui

from src.ui.pages.gestiones import register_gestiones_page
from src.ui.pages.gestiones_detalle import register_gestiones_detalle_page
from src.ui.pages.gestiones_nueva import register_gestiones_nueva_page
from src.ui.pages.home import register_home_page
from src.ui.pages.login import register_login_page
from src.ui.pages.pagos import register_pagos_page
from src.ui.pages.periodos import register_periodos_page
from src.ui.pages.register import register_register_page
from src.ui.pages.reportes import register_reportes_page
from src.ui.pages.catalogos import register_catalogos_page
from src.ui.pages.documentos import register_documentos_page
from src.ui.pages.grupos import register_grupos_page
# ── Dark theme CSS overrides ─────────────────────────────────────────────────
ui.add_head_html(
    """
<style>
body { background-color: #1a1a2e !important; color: #e0e0e0; }
.q-header { background-color: #16213e !important; }
.q-drawer { background-color: #0f3460 !important; }
</style>
""",
    shared=True,
)

# ── Page registrations ────────────────────────────────────────────────────────
register_login_page()
register_register_page()
register_home_page()
register_gestiones_page()
register_gestiones_nueva_page()
register_gestiones_detalle_page()
register_pagos_page()
register_periodos_page()
register_grupos_page()
register_catalogos_page()
register_reportes_page()
register_documentos_page()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="Gestiones SOS",
        port=8080,
        reload=False,
        storage_secret=os.environ.get(
            "STORAGE_SECRET", os.environ.get("JWT_SECRET", "")
        ),
    )
