"""Grupos page — list + create for GroupClaim entities with claim stats."""

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

            # ── Create form ────────────────────────────────────────────────

            with ui.card().classes("w-full p-4 mb-6"):
                ui.label("Nuevo Grupo").classes("text-lg font-bold mb-2")

                with ui.row().classes("w-full gap-4"):
                    name_input = ui.input(
                        label="Nombre del grupo",
                        placeholder="Ej: SOS Cobranzas",
                    ).classes("flex-1")
                    desc_input = ui.input(
                        label="Descripción",
                        placeholder="Opcional",
                    ).classes("flex-1")

                with ui.row().classes("items-center gap-2"):
                    ui.button("Agregar", icon="add", on_click=_add_group)

            # ── Group list with stats ──────────────────────────────────────

            @ui.refreshable
            def _render_grupos() -> None:
                groups = container.obtener_grupos.execute()
                claims = container.claim_repo.get_all()

                # Aggregate stats per group
                stats: dict[UUID | None, dict] = {}
                for g in groups:
                    stats[g.group_id] = {"count": 0, "total": 0.0}
                for c in claims:
                    gid = c.group_id
                    if gid not in stats:
                        stats[gid] = {"count": 0, "total": 0.0}
                    stats[gid]["count"] += 1
                    stats[gid]["total"] += c.claimed_amount

                # Header row
                with ui.row().classes(
                    "items-center gap-4 py-2 border-b border-gray-600 font-bold w-full"
                ):
                    ui.label("Nombre").classes("text-xs w-40")
                    ui.label("Descripción").classes("text-xs w-48")
                    ui.label("Gestiones").classes("text-xs w-20 text-center")
                    ui.label("Monto Total").classes("text-xs w-28 text-right")
                    ui.label("").classes("w-20")

                # Data rows
                for g in groups:
                    s = stats.get(g.group_id, {"count": 0, "total": 0.0})
                    with ui.row().classes(
                        "items-center gap-4 py-1 hover:bg-gray-800 w-full"
                    ):
                        ui.label(g.name).classes("text-sm w-40")
                        ui.label(g.description or "—").classes(
                            "text-sm w-48 text-gray-400"
                        )
                        ui.label(str(s["count"])).classes(
                            "text-sm w-20 text-center"
                        )
                        ui.label(f"${s['total']:,.2f}").classes(
                            "text-sm w-28 text-right"
                        )
                        ui.button(
                            "Eliminar",
                            icon="delete",
                            on_click=lambda gid=g.group_id: _delete_group(gid),
                        ).props("flat size=sm dense color=negative")

            @with_audit_user
            async def _add_group() -> None:
                name = (name_input.value or "").strip()
                if not name:
                    ui.notify("El nombre del grupo es requerido", type="warning")
                    return
                desc = (desc_input.value or "").strip() or None
                container.registrar_grupo.execute(name, description=desc)
                name_input.value = ""
                desc_input.value = ""
                _render_grupos.refresh()

            @with_audit_user
            def _delete_group(group_id: UUID) -> None:
                try:
                    container.eliminar_grupo.execute(group_id)
                except ValueError as e:
                    ui.notify(str(e), type="negative")
                _render_grupos.refresh()

            _render_grupos()
