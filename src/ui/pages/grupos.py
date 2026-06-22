"""Grupos page — list + inline create for GroupClaim entities."""

from uuid import UUID

from nicegui import ui

from src.infrastructure.container import Container
from src.ui.components.shell import AppShell
from src.ui.services.audit_helper import with_audit_user


def register_grupos_page() -> None:
    @ui.page("/grupos")
    def grupos_page() -> None:
        with AppShell():
            container = Container.get_instance()

            ui.label("Grupos").classes("text-2xl font-bold")

            # ── Inline create form ──────────────────────────────────────────

            name_input = ui.input(
                label="Nombre del grupo", placeholder="Ingrese nombre..."
            )

            @with_audit_user
            async def _add_group() -> None:
                name = name_input.value.strip()
                if name:
                    container.registrar_grupo.execute(name)
                    name_input.value = ""
                    _render_grupos.refresh()

            ui.button("Agregar", icon="add", on_click=_add_group)

            # ── Group list table ────────────────────────────────────────────

            @ui.refreshable
            def _render_grupos() -> None:
                groups = container.obtener_grupos.execute()

                columns = [
                    {
                        "name": "name",
                        "label": "Nombre",
                        "field": "name",
                        "align": "left",
                    },
                ]
                rows = [{"name": g.name, "group_id": str(g.group_id)} for g in groups]
                ui.table(columns=columns, rows=rows, row_key="group_id").classes(
                    "w-full mt-4"
                )

                # Inline delete buttons below the table
                for g in groups:
                    with ui.row().classes("items-center gap-4"):
                        ui.label(g.name).classes("text-sm text-gray-400 w-48")
                        ui.button(
                            "Eliminar",
                            icon="delete",
                            on_click=lambda gid=g.group_id: _delete_group(gid),
                        ).props("flat size=sm")

            @with_audit_user
            def _delete_group(group_id: UUID) -> None:
                try:
                    container.eliminar_grupo.execute(group_id)
                except ValueError as e:
                    ui.notify(str(e), type="negative")
                _render_grupos.refresh()

            _render_grupos()
