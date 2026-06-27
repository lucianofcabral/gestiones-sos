"""Grupos page — list + create for GroupClaim entities with claim stats."""

from uuid import UUID

from nicegui import ui

from src.application.use_cases.claims.actualizar_grupo_de_gestion import (
    ActualizarGrupoDeGestionInput,
)
from src.domain.models.entities import Claim, GroupClaim
from src.infrastructure.container import Container
from src.ui.components.shell import AppShell
from src.ui.services.audit_helper import with_audit_user


def register_grupos_page() -> None:
    @ui.page("/grupos")
    def grupos_page() -> None:
        with AppShell():
            container = Container.get_instance()

            ui.label("Grupos").classes("text-2xl font-bold")

            # ── Group actions (defined before UI to avoid UnboundLocalError) ──

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

            def _edit_group(group: GroupClaim) -> None:
                """Open an edit dialog for the group with member management."""

                with ui.dialog() as dlg, ui.card().classes("w-[600px] max-w-full"):
                    # ── State ─────────────────────────────────────────────
                    available_select: ui.select | None = None

                    def _claims_in_group() -> list[Claim]:
                        return [
                            c for c in container.claim_repo.get_all()
                            if c.group_id == group.group_id
                        ]

                    def _claims_available() -> list[Claim]:
                        return [
                            c for c in container.claim_repo.get_all()
                            if c.group_id != group.group_id
                        ]

                    def _rebuild_members() -> None:
                        members_container.clear()
                        members = _claims_in_group()
                        with members_container:
                            ui.label(f"Gestiones ({len(members)})").classes(
                                "text-sm font-bold mb-1"
                            )
                            if not members:
                                ui.label(
                                    "No hay gestiones en este grupo."
                                ).classes("text-sm text-gray-400 italic")
                            for cm in members:
                                with ui.row().classes(
                                    "items-center gap-2 py-1 w-full"
                                ):
                                    ui.label(
                                        f"{cm.claimer_name} — {cm.policy_number} — {cm.plate}"
                                    ).classes("text-sm flex-1")
                                    ui.button(
                                        "Quitar",
                                        icon="remove_circle",
                                        on_click=lambda cid=cm.claim_id: _remove(
                                            cid
                                        ),
                                    ).props(
                                        "flat size=sm dense color=negative"
                                    )

                    def _rebuild_available() -> None:
                        avail = _claims_available()
                        if available_select is not None:
                            available_select.options = {
                                str(c.claim_id): (
                                    f"{c.claimer_name} — "
                                    f"{c.policy_number} — {c.plate}"
                                )
                                for c in avail
                            }
                        add_row.set_visibility(len(avail) > 0)

                    def _remove(claim_id: UUID) -> None:
                        try:
                            container.actualizar_grupo_de_gestion.execute(
                                ActualizarGrupoDeGestionInput(
                                    claim_id=claim_id, new_group_id=None
                                )
                            )
                            ui.notify("Gestión quitada del grupo", type="positive")
                        except Exception as e:
                            ui.notify(f"Error: {e}", type="negative")
                        _rebuild_members()
                        _rebuild_available()

                    def _add() -> None:
                        if available_select is None or not available_select.value:
                            return
                        try:
                            container.actualizar_grupo_de_gestion.execute(
                                ActualizarGrupoDeGestionInput(
                                    claim_id=UUID(available_select.value),
                                    new_group_id=group.group_id,
                                )
                            )
                            ui.notify("Gestión agregada al grupo", type="positive")
                        except Exception as e:
                            ui.notify(f"Error: {e}", type="negative")
                        available_select.value = None
                        _rebuild_members()
                        _rebuild_available()

                    # ── Header ──────────────────────────────────────────────
                    ui.label(f"Editar Grupo: {group.name}").classes(
                        "text-lg font-bold mb-2"
                    )

                    # ── Basic info ──────────────────────────────────────────
                    with ui.row().classes("w-full gap-4"):
                        name_inp = ui.input(
                            label="Nombre", value=group.name,
                        ).classes("flex-1")
                        desc_inp = ui.input(
                            label="Descripción", value=group.description or "",
                        ).classes("flex-1")

                    ui.separator().classes("my-2")

                    # ── Members list ────────────────────────────────────────
                    members_container = ui.column().classes("w-full")
                    _rebuild_members()

                    ui.separator().classes("my-2")

                    # ── Add claim ───────────────────────────────────────────
                    add_row = ui.row().classes("items-center gap-2 w-full")
                    with add_row:
                        available_select = ui.select(
                            label="Agregar gestión...",
                            options={},
                            with_input=True,
                        ).classes("flex-1")
                        ui.button(
                            "Agregar",
                            icon="add",
                            on_click=lambda: _add(),
                        ).props("flat size=sm dense")
                    _rebuild_available()

                    # ── Save / Cancel ───────────────────────────────────────
                    with ui.row().classes("gap-2 justify-end mt-2"):
                        ui.button("Cancelar", on_click=dlg.close).props("flat")

                        @with_audit_user
                        async def _save(d=dlg, gid=group.group_id) -> None:
                            name = (name_inp.value or "").strip()
                            if not name:
                                ui.notify(
                                    "El nombre es requerido", type="warning"
                                )
                                return
                            desc = (desc_inp.value or "").strip() or None
                            result = container.actualizar_grupo.execute(
                                gid, name, description=desc
                            )
                            if result is None:
                                ui.notify(
                                    "Grupo no encontrado", type="negative"
                                )
                            else:
                                ui.notify(
                                    "Grupo actualizado", type="positive"
                                )
                            d.close()
                            _render_grupos.refresh()

                        ui.button("Guardar", on_click=_save)

                dlg.open()

            @with_audit_user
            def _delete_group(group_id: UUID) -> None:
                try:
                    result = container.eliminar_grupo.execute(group_id)
                    if result:
                        ui.notify("Grupo eliminado", type="positive")
                    else:
                        ui.notify("Grupo no encontrado", type="warning")
                except ValueError as e:
                    ui.notify(str(e), type="negative")
                _render_grupos.refresh()

            # ── Sorting state ─────────────────────────────────────────────────
            _sort_col = 0
            _sort_dir = 1

            def _sort(col_idx: int) -> None:
                nonlocal _sort_col, _sort_dir
                if _sort_col == col_idx:
                    _sort_dir *= -1
                else:
                    _sort_col = col_idx
                    _sort_dir = 1
                _render_grupos.refresh()

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
                nonlocal _sort_col, _sort_dir
                groups = [g for g in container.obtener_grupos.execute() if g.active]
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

                # Sort
                _col_keys = [
                    lambda g: g.name,
                    lambda g: g.description or "",
                    lambda g: stats.get(g.group_id, {"count": 0})["count"],
                    lambda g: stats.get(g.group_id, {"total": 0.0})["total"],
                    lambda g: "",
                ]
                groups = sorted(
                    groups, key=_col_keys[_sort_col], reverse=_sort_dir == -1
                )

                # Header row
                _col_labels = [
                    ("Nombre", "text-xs w-40"),
                    ("Descripción", "text-xs w-48"),
                    ("Gestiones", "text-xs w-20 text-center"),
                    ("Monto Total", "text-xs w-28 text-right"),
                    ("Acciones", "text-xs w-28"),
                ]
                with ui.row().classes(
                    "items-center gap-4 py-2 border-b border-gray-600 font-bold w-full"
                ):
                    for i, (label, cls) in enumerate(_col_labels):
                        arrow = (
                            " ▲" if _sort_col == i and _sort_dir == 1
                            else " ▼" if _sort_col == i
                            else ""
                        )
                        ui.label(f"{label}{arrow}").classes(
                            f"{cls} cursor-pointer"
                        ).on("click", lambda i=i: _sort(i))

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
                        with ui.row().classes("gap-1"):
                            ui.button(
                                "Editar",
                                icon="edit",
                                on_click=lambda g=g: _edit_group(g),
                            ).props("flat size=sm dense")
                            ui.button(
                                "Eliminar",
                                icon="delete",
                                on_click=lambda gid=g.group_id: _delete_group(gid),
                            ).props("flat size=sm dense color=negative")

            _render_grupos()
