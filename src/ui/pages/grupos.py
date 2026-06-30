"""Grupos page — list, create, edit groups with claim management and documents."""

from collections.abc import Callable
from uuid import UUID

from nicegui import ui

from src.application.use_cases.claims.actualizar_grupo_de_gestion import (
    ActualizarGrupoDeGestionInput,
)
from src.domain.enums import DocumentTypeEnum
from src.domain.models.entities import Claim, GroupClaim
from src.infrastructure.container import Container
from src.ui.components.document_upload import DocumentUpload
from src.ui.components.shell import AppShell
from src.ui.services.audit_helper import with_audit_user


# ── Reusable group edit dialog ─────────────────────────────────────────────────


def edit_group_dialog(
    group: GroupClaim, container: Container, refresh_fn: Callable
) -> None:
    """Open the group edit dialog. Extracted for reuse from documentos.py."""
    with ui.dialog() as dlg, ui.card().classes("w-[700px] max-w-full"):
        available_select: ui.select | None = None
        doc_refresh_ref = {"fn": None}

        def _claims_in_group() -> list[Claim]:
            return [
                c
                for c in container.claim_repo.get_all()
                if c.group_id == group.group_id
            ]

        def _claims_available() -> list[Claim]:
            return [
                c
                for c in container.claim_repo.get_all()
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
                    ui.label("No hay gestiones en este grupo.").classes(
                        "text-sm text-gray-400 italic"
                    )
                for cm in members:
                    with ui.row().classes("items-center gap-2 py-1 w-full"):
                        ui.label(
                            f"{cm.claimer_name} — "
                            f"{cm.policy_number} — {cm.plate}"
                        ).classes("text-sm flex-1")
                        ui.button(
                            "Quitar",
                            icon="remove_circle",
                            on_click=lambda cid=cm.claim_id: (
                                _remove_claim_dialog(cid, cm)
                            ),
                        ).props("flat size=sm dense color=negative")

        def _rebuild_available() -> None:
            avail = _claims_available()
            if available_select is not None:
                available_select.options = {
                    str(c.claim_id): (
                        f"{c.claimer_name} — {c.policy_number} — {c.plate}"
                    )
                    for c in avail
                }
            add_row.set_visibility(len(avail) > 0)

        def _remove_claim_dialog(
            claim_id: UUID,
            claim: Claim,
        ) -> None:
            with (
                ui.dialog() as rm_dlg,
                ui.card().classes("w-[400px] max-w-full"),
            ):
                ui.label("Quitar gestión del grupo").classes(
                    "text-lg font-bold mb-2"
                )
                ui.label(
                    f"{claim.claimer_name} — "
                    f"{claim.policy_number} — {claim.plate}"
                ).classes("text-sm text-gray-400 mb-4")

                ui.label("¿Qué querés hacer con esta gestión?").classes(
                    "text-sm mb-3"
                )

                @with_audit_user
                def _just_remove() -> None:
                    try:
                        container.actualizar_grupo_de_gestion.execute(
                            ActualizarGrupoDeGestionInput(
                                claim_id=claim_id,
                                new_group_id=None,
                            )
                        )
                        ui.notify(
                            "Gestión quitada del grupo",
                            type="positive",
                        )
                    except Exception as e:
                        ui.notify(f"Error: {e}", type="negative")
                    rm_dlg.close()
                    _rebuild_members()
                    _rebuild_available()

                @with_audit_user
                def _remove_and_inactivate() -> None:
                    try:
                        container.actualizar_grupo_de_gestion.execute(
                            ActualizarGrupoDeGestionInput(
                                claim_id=claim_id,
                                new_group_id=None,
                            )
                        )
                        container.claim_repo.inactivate(claim_id)
                        ui.notify(
                            "Gestión quitada del grupo e inactivada",
                            type="positive",
                        )
                    except Exception as e:
                        ui.notify(f"Error: {e}", type="negative")
                    rm_dlg.close()
                    _rebuild_members()
                    _rebuild_available()

                with ui.row().classes("gap-2 justify-end mt-2"):
                    ui.button(
                        "Solo quitar del grupo",
                        on_click=_just_remove,
                    ).props("flat")
                    ui.button(
                        "Quitar e inactivar",
                        icon="block",
                        on_click=_remove_and_inactivate,
                    ).props("flat color=negative")
                    ui.button(
                        "Cancelar",
                        on_click=rm_dlg.close,
                    ).props("flat")
            rm_dlg.open()

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

        # ── Dialog body ────────────────────────────────────────────
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(f"Editar Grupo: {group.name}").classes(
                "text-lg font-bold"
            )

        with ui.row().classes("w-full gap-4 mt-2"):
            name_inp = ui.input(
                label="Nombre",
                value=group.name,
            ).classes("flex-1")
            desc_inp = ui.input(
                label="Descripción",
                value=group.description or "",
            ).classes("flex-1")

        ui.separator().classes("my-2")

        # ── Members ────────────────────────────────────────────────
        members_container = ui.column().classes("w-full")
        _rebuild_members()

        ui.separator().classes("my-2")

        # ── Add claim ──────────────────────────────────────────────
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

        ui.separator().classes("my-2")

        # ── Documents ──────────────────────────────────────────────
        ui.label("Documentos").classes("text-sm font-bold mb-1")

        def _render_docs() -> None:
            doc_area.clear()
            with doc_area:
                docs = container.obtener_documentos.by_entity(
                    DocumentTypeEnum.GROUP_CLAIM.value,
                    group.group_id,
                )
                if docs:
                    for d in docs:
                        with ui.row().classes("items-center gap-2 py-1"):
                            ui.label(d.name).classes("text-sm flex-1")
                            ui.label(f"{d.size // 1024}KB").classes(
                                "text-xs text-gray-400"
                            )
                else:
                    ui.label("Sin documentos.").classes(
                        "text-sm text-gray-400 italic"
                    )

        doc_area = ui.column().classes("w-full")
        _render_docs()

        DocumentUpload(
            entity_type=DocumentTypeEnum.GROUP_CLAIM.value,
            entity_id=group.group_id,
            on_upload=_render_docs,
        ).render()

        # ── Save / Cancel ──────────────────────────────────────────
        with ui.row().classes("gap-2 justify-end mt-2"):
            ui.button("Cancelar", on_click=dlg.close).props("flat")

            @with_audit_user
            async def _save(d=dlg, gid=group.group_id) -> None:
                name = (name_inp.value or "").strip()
                if not name:
                    ui.notify("El nombre es requerido", type="warning")
                    return
                desc = (desc_inp.value or "").strip() or None
                result = container.actualizar_grupo.execute(
                    gid, name, description=desc
                )
                if result is None:
                    ui.notify("Grupo no encontrado", type="negative")
                else:
                    ui.notify("Grupo actualizado", type="positive")
                d.close()
                refresh_fn()

            ui.button("Guardar", on_click=_save)

    dlg.open()


def register_grupos_page() -> None:
    @ui.page("/grupos")
    def grupos_page() -> None:
        with AppShell():
            container = Container.get_instance()

            ui.label("Grupos").classes("text-2xl font-bold")

            # ── Actions ────────────────────────────────────────────────────────

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
                edit_group_dialog(group, container, _render_grupos.refresh)

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

            # ── Sorting ────────────────────────────────────────────────────────
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

            # ── Filters ────────────────────────────────────────────────────────
            filter_name = ui.input(
                placeholder="Filtrar por nombre...",
                on_change=lambda: _render_grupos.refresh(),
            ).classes("w-64")

            show_inactive = ui.checkbox(
                "Mostrar inactivos",
                on_change=lambda: _render_grupos.refresh(),
            )

            # ── Create form ────────────────────────────────────────────────────
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

            # ── Group list ─────────────────────────────────────────────────────
            @ui.refreshable
            def _render_grupos() -> None:
                nonlocal _sort_col, _sort_dir
                name_filter = (filter_name.value or "").strip().lower()

                all_groups = container.obtener_grupos.execute()
                groups = []
                for g in all_groups:
                    if not g.active and not show_inactive.value:
                        continue
                    if name_filter and name_filter not in g.name.lower():
                        continue
                    groups.append(g)

                claims = container.claim_repo.get_all()

                stats: dict[UUID | None, dict] = {}
                for g in groups:
                    stats[g.group_id] = {"count": 0, "total": 0.0}
                for c in claims:
                    gid = c.group_id
                    if gid not in stats:
                        stats[gid] = {"count": 0, "total": 0.0}
                    stats[gid]["count"] += 1
                    stats[gid]["total"] += c.claimed_amount

                _col_keys = [
                    lambda g: g.name,
                    lambda g: g.created_at or "",
                    lambda g: g.description or "",
                    lambda g: stats.get(g.group_id, {"count": 0})["count"],
                    lambda g: stats.get(g.group_id, {"total": 0.0})["total"],
                    lambda g: "",
                ]
                groups = sorted(
                    groups,
                    key=_col_keys[_sort_col],
                    reverse=_sort_dir == -1,
                )

                # Define table columns
                table_columns = [
                    {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre', 'align': 'left', 'sortable': True},
                    {'name': 'creado', 'label': 'Creado', 'field': 'creado', 'align': 'left', 'sortable': True},
                    {'name': 'descripcion', 'label': 'Descripción', 'field': 'descripcion', 'align': 'left', 'sortable': True},
                    {'name': 'cant_gestiones', 'label': 'Gestiones', 'field': 'cant_gestiones', 'align': 'center', 'sortable': True},
                    {'name': 'monto_total', 'label': 'Monto Total', 'field': 'monto_total', 'align': 'right', 'sortable': True},
                    {'name': 'acciones', 'label': 'Acciones', 'field': 'acciones', 'align': 'center', 'sortable': False},
                ]
                
                # Prepare table data
                table_rows = []
                for g in groups:
                    s = stats.get(g.group_id, {"count": 0, "total": 0.0})
                    table_rows.append({
                        'id': str(g.group_id),
                        'group_id': g.group_id,
                        'nombre': g.name,
                        'creado': g.created_at.strftime('%Y-%m-%d') if g.created_at else '—',
                        'descripcion': g.description or '—',
                        'cant_gestiones': str(s['count']),
                        'monto_total': f"${s['total']:,.2f}",
                    })
                
                # Create table
                table = ui.table(columns=table_columns, rows=table_rows, row_key='id').classes('w-full')
                
                # Add action buttons slot
                table.add_slot('body-cell-acciones', '''
                    <q-td :props="props" class="text-center">
                        <q-btn label="Editar" icon="edit" @click="$parent.$emit('edit', props.row)" flat dense color="blue" size="sm" />
                        <q-btn label="Eliminar" icon="delete" @click="$parent.$emit('delete', props.row)" flat dense color="red" size="sm" />
                    </q-td>
                ''')
                
                # Register event handlers
                def _handle_edit(row: dict) -> None:
                    group_id = row.get('group_id')
                    if group_id:
                        g = container.group_claim_repo.get_by_id(group_id)
                        if g:
                            _edit_group(g)
                
                def _handle_delete(row: dict) -> None:
                    group_id = row.get('group_id')
                    if group_id:
                        _delete_group(group_id)
                
                table.on('edit', lambda e: _handle_edit(e.args))
                table.on('delete', lambda e: _handle_delete(e.args))

            _render_grupos()
