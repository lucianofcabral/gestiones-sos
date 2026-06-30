"""Gestiones list page — sortable, paginated table with compact filters."""

import math
from uuid import UUID

from nicegui import ui

from src.application.use_cases.claims.eliminar_gestion_sos import (
    EliminarGestionSOSInput,
)
from src.application.use_cases.claims.eliminar_grouped_claim import (
    EliminarGroupedClaimInput,
)
from src.application.use_cases.claims.obtener_gestiones import (
    ObtenerGestionesInput,
)
from src.domain.exceptions import ClaimHasActivePaymentsError, ClaimNotFoundError
from src.infrastructure.container import Container
from src.ui.components.shell import AppShell
from src.ui.pages.gestiones_nueva import nueva_gestion_dialog
from src.ui.pages.sos_import import importar_gestiones_dialog
from src.ui.services.audit_helper import with_audit_user

_PAGE_SIZE = 12


def _prepare_gestiones_data(container: Container) -> list[dict]:
    """
    Prepare gestiones table data by pre-computing all lookups in one pass.
    
    Returns list of dicts with fields:
        id, claim_id, tipo, gestion, asegurado, poliza, patente, monto,
        fecha, resuelto, cant_pagos, active, has_group, has_nc, solved
    
    Complexity: O(N) where N = number of claims (one pass per repository).
    """
    # Fetch all claims
    all_claims = container.claim_repo.get_all()
    if not all_claims:
        return []
    
    # Pre-fetch all claim kinds
    all_kinds = {k.claim_kind_id: k.name for k in container.claim_kind_repo.get_all()}
    
    # Pre-compute SOS data (gestion numbers)
    sos_map = {}
    for sos in container.sos_claim_repo.get_all():
        sos_map[sos.claim_id] = sos
    
    # Pre-compute payment counts and NC flags (avoid N+1)
    payment_counts = {}
    has_nc_map = {}
    
    all_payments = container.payment_repo.get_all()
    for claim in all_claims:
        claim_payments = [p for p in all_payments if p.claim_id == claim.claim_id]
        payment_counts[claim.claim_id] = len(claim_payments)
        
        # Check if any payment has an associated NC
        has_nc = False
        for payment in claim_payments:
            try:
                nc = container.obtener_ncs.get_by_payment_id(payment.payment_id)
                if nc is not None:
                    has_nc = True
                    break
            except Exception:
                pass
        has_nc_map[claim.claim_id] = has_nc
    
    # Build rows
    rows = []
    for claim in all_claims:
        sos = sos_map.get(claim.claim_id)
        
        row = {
            'id': str(claim.claim_id),
            'claim_id': claim.claim_id,
            'tipo': all_kinds.get(claim.claim_kind_id, '—'),
            'gestion': sos.gestion if sos else '—',
            'asegurado': claim.claimer_name,
            'poliza': claim.policy_number,
            'patente': claim.plate,
            'monto': f'{claim.claimed_amount:,.2f}',
            'fecha': claim.created_at.strftime('%d/%m/%Y'),
            'resuelto': '✓' if claim.solved else '—',
            'cant_pagos': payment_counts[claim.claim_id],
            'active': claim.active,
            'has_group': claim.group_id is not None,
            'has_nc': has_nc_map[claim.claim_id],
            'solved': claim.solved,
        }
        rows.append(row)
    
    return rows


# ── Table Column Definitions ────────────────────────────────────────

GESTIONES_COLUMNS = [
    {
        'name': 'tipo',
        'label': 'Tipo',
        'field': 'tipo',
        'align': 'left',
        'sortable': True,
        'style': 'min-width: 80px;'
    },
    {
        'name': 'gestion',
        'label': 'Gestión/Ref.',
        'field': 'gestion',
        'align': 'left',
        'sortable': True,
        'style': 'min-width: 96px;'
    },
    {
        'name': 'asegurado',
        'label': 'Asegurado',
        'field': 'asegurado',
        'align': 'left',
        'sortable': True,
        'style': 'flex: 1; min-width: 170px;'
    },
    {
        'name': 'poliza',
        'label': 'Póliza',
        'field': 'poliza',
        'align': 'left',
        'sortable': True,
        'style': 'min-width: 112px;'
    },
    {
        'name': 'patente',
        'label': 'Patente',
        'field': 'patente',
        'align': 'left',
        'sortable': True,
        'style': 'min-width: 96px;'
    },
    {
        'name': 'monto',
        'label': 'Monto',
        'field': 'monto',
        'align': 'right',
        'sortable': True,
        'style': 'min-width: 112px;'
    },
    {
        'name': 'fecha',
        'label': 'Fecha',
        'field': 'fecha',
        'align': 'left',
        'sortable': True,
        'style': 'min-width: 112px;'
    },
    {
        'name': 'resuelto',
        'label': 'Resuelto',
        'field': 'resuelto',
        'align': 'center',
        'sortable': True,
        'style': 'min-width: 80px;'
    },
    {
        'name': 'cant_pagos',
        'label': 'Cant. Pagos',
        'field': 'cant_pagos',
        'align': 'center',
        'sortable': True,
        'style': 'min-width: 80px;'
    },
    {
        'name': 'acciones',
        'label': 'Acciones',
        'field': 'acciones',
        'align': 'center',
        'sortable': False,
        'style': 'min-width: 160px;'
    },
]


# ── Action Icons (Gestiones Row) ────────────────────────────────────

def _apply_filters_to_prepared_data(
    rows: list[dict],
    filter_kind: str | None,
    filter_text: str | None,
    filter_solved: bool,
    filter_has_payments: bool,
    filter_no_payments: bool,
    filter_has_nc: bool,
    filter_no_nc: bool,
    show_inactive: bool,
) -> list[dict]:
    """Apply all filters to prepared gestiones data."""
    result = rows
    
    # Filter by claim kind
    if filter_kind:
        result = [r for r in result if r['tipo'] == filter_kind]
    
    # Filter by text (policy, customer, plate, gestion)
    # Ensure all values are converted to strings and lowercase for safe comparison
    if filter_text:
        q = filter_text.lower()
        result = [
            r for r in result
            if (q in str(r.get('poliza') or '').lower()
                or q in str(r.get('asegurado') or '').lower()
                or q in str(r.get('patente') or '').lower()
                or q in str(r.get('gestion') or '').lower())
        ]
    
    # Filter by solved status
    if filter_solved:
        result = [r for r in result if r['solved']]
    
    # Filter by payment status
    if filter_has_payments:
        result = [r for r in result if r['cant_pagos'] > 0]
    if filter_no_payments:
        result = [r for r in result if r['cant_pagos'] == 0]
    
    # Filter by NC status
    if filter_has_nc:
        result = [r for r in result if r['has_nc']]
    if filter_no_nc:
        result = [r for r in result if not r['has_nc']]
    
    # Filter by active status
    if not show_inactive:
        result = [r for r in result if r['active']]
    
    return result


def _sort_prepared_data(rows: list[dict], sort_col: int, sort_dir: int) -> list[dict]:
    """Sort prepared data by column index."""
    def parse_monto(monto_str: str) -> float:
        """Parse monto string to float, handling '$' and ',' separators."""
        try:
            # Remove $ and , characters, then convert to float
            return float(monto_str.replace('$', '').replace(',', ''))
        except (ValueError, AttributeError):
            return 0.0
    
    # Define sort keys matching GESTIONES_COLUMNS order
    sort_keys = [
        lambda r: r['tipo'],           # 0: tipo
        lambda r: str(r['gestion']),   # 1: gestion
        lambda r: r['asegurado'],      # 2: asegurado
        lambda r: r['poliza'],         # 3: poliza
        lambda r: r['patente'],        # 4: patente
        lambda r: parse_monto(r['monto']),  # 5: monto
        lambda r: r['fecha'],          # 6: fecha
        lambda r: r['resuelto'],       # 7: resuelto
        lambda r: r['cant_pagos'],     # 8: cant_pagos
        lambda r: '',                  # 9: acciones (not sortable)
    ]
    
    if sort_col >= len(sort_keys):
        return rows
    
    return sorted(rows, key=sort_keys[sort_col], reverse=sort_dir == -1)


def _render_gestiones_actions(claim_id: UUID, row_data: dict) -> None:
    """
    Render action icons for a gestiones row.
    
    CRITICAL: NO row-click behavior. All navigation via edit icon.
    
    Args:
        claim_id: UUID of the claim
        row_data: Dict with keys: has_group, solved, has_nc, active
    """
    from src.ui.components.table_helpers import ActionButton
    
    def _open_delete_dialog() -> None:
        """Open delete confirmation dialog."""
        with ui.dialog() as delete_dialog:
            with delete_dialog, ui.card().classes("p-4 min-w-96"):
                ui.label("Eliminar Gestión").classes("text-lg font-bold")
                ui.label(f"¿Está seguro de eliminar esta gestión?")
                
                with ui.row().classes("gap-2 justify-end mt-4"):
                    ui.button("Cancelar", on_click=delete_dialog.close).props("flat")
                    ui.button(
                        "Eliminar",
                        on_click=lambda: _delete_gestion_impl(claim_id, delete_dialog)
                    )
        
        delete_dialog.open()
    
    def _delete_gestion_impl(cid: UUID, dialog: ui.dialog) -> None:
        """Execute delete operation."""
        try:
            # Determine claim kind and call appropriate delete use case
            claim = container.claim_repo.get_by_id(cid)
            if not claim:
                ui.notify("Gestión no encontrada", type="negative")
                dialog.close()
                return
            
            # Get claim kind to determine which delete to call
            kind = container.claim_kind_repo.get_by_id(claim.claim_kind_id)
            kind_name = kind.name if kind else "Unknown"
            
            if kind_name.upper() == "SOS":
                container.eliminar_gestion_sos.execute(
                    EliminarGestionSOSInput(claim_id=cid)
                )
            else:
                container.eliminar_grouped_claim.execute(
                    EliminarGroupedClaimInput(claim_id=cid)
                )
            
            ui.notify("Gestión eliminada", type="positive")
            _render_gestiones.refresh()
        except ClaimHasActivePaymentsError as e:
            ui.notify(str(e), type="negative")
        except ClaimNotFoundError as e:
            ui.notify(str(e), type="negative")
        except Exception as e:
            ui.notify(f"Error: {e}", type="negative")
        finally:
            dialog.close()
    
    with ui.row().classes("gap-1 items-center no-wrap"):
        # Edit icon (always visible) → navigate to edit page
        ActionButton(
            icon='edit',
            label='Editar',
            on_click=lambda cid=claim_id: ui.navigate.to(f'/gestiones/{cid}'),
            color='text-blue-500'
        )
        
        # Grupo icon (conditional: only if claim has group_id)
        if row_data.get('has_group'):
            ActionButton(
                icon='group',
                label='Editar Grupo',
                on_click=lambda: ui.notify("Grupo dialog - TBD", type="info"),
                color='text-purple-500'
            )
        
        # Pagos icon (conditional: only if not solved)
        if not row_data.get('solved'):
            ActionButton(
                icon='add_circle',
                label='Registrar Pago',
                on_click=lambda: ui.notify("Payment dialog - TBD", type="info"),
                color='text-green-500'
            )
        
        # NC icon (conditional: only if has NC)
        if row_data.get('has_nc'):
            ActionButton(
                icon='receipt',
                label='Crédito',
                on_click=lambda: ui.notify("NC dialog - TBD", type="info"),
                color='text-orange-500'
            )
        
        # Delete icon (always visible)
        ActionButton(
            icon='delete',
            label='Eliminar',
            on_click=_open_delete_dialog,
            color='text-red-500'
        )


def register_gestiones_page() -> None:
    @ui.page("/gestiones")
    def gestiones_page() -> None:
        with AppShell():
            container = Container.get_instance()

            ui.label("Gestiones").classes("text-2xl font-bold")

            # ── Action buttons ─────────────────────────────────────────────────
            with ui.row().classes("items-center gap-2 mt-2"):
                ui.button(
                    "Nueva Gestión",
                    icon="add",
                    on_click=lambda: nueva_gestion_dialog(
                        on_success=lambda: _render_gestiones.refresh()
                    ),
                ).props("flat color=white")
                ui.button(
                    "Importar",
                    icon="cloud_upload",
                    on_click=lambda: importar_gestiones_dialog(
                        on_success=lambda: _render_gestiones.refresh()
                    ),
                ).props("flat color=white")

            # ── Filters ────────────────────────────────────────────────────────
            kind_options = _get_kind_options(container)

            with ui.card().classes("w-full p-3 mt-2"):
                with ui.row().classes("items-center gap-3 w-full"):
                    filter_kind = ui.select(
                        label="Tipo", options=kind_options,
                        with_input=True, clearable=True,
                    ).classes("w-36")
                    filter_text = ui.input(
                        label="Buscar",
                        placeholder="Cliente, dominio, N° gestión, póliza...",
                    ).props("dense outlined").classes("flex-1 min-w-[200px]")
                    toggle = ui.switch("Mostrar inactivos", value=False)

                with ui.row().classes("items-center gap-4 mt-1"):
                    filter_solved = ui.checkbox("Resuelta")
                    filter_has_payments = ui.checkbox("Tiene pagos")
                    filter_no_payments = ui.checkbox("No tiene pagos")
                    filter_has_nc = ui.checkbox("Tiene NC")
                    filter_no_nc = ui.checkbox("No tiene NC")

            for f in [filter_kind, filter_text, filter_solved,
                      filter_has_payments, filter_no_payments,
                      filter_has_nc, filter_no_nc, toggle]:
                f.on("update:model-value", lambda: (_reset_page(), _render_gestiones.refresh()))

            # ── Sorting & pagination state ────────────────────────────────────
            _sort_col = 0
            _sort_dir = 1
            _page = 1

            def _reset_page() -> None:
                nonlocal _page
                _page = 1

            # ── Delete handler (inner scope for access to _render_gestiones) ───
            def _delete_gestion(claim_id: UUID) -> None:
                """Open delete confirmation dialog."""
                with ui.dialog() as delete_dialog:
                    with delete_dialog, ui.card().classes("p-4 min-w-96"):
                        ui.label("Eliminar Gestión").classes("text-lg font-bold")
                        ui.label("¿Está seguro de eliminar esta gestión?")
                        
                        with ui.row().classes("gap-2 justify-end mt-4"):
                            ui.button("Cancelar", on_click=delete_dialog.close).props("flat")
                            ui.button(
                                "Eliminar",
                                on_click=lambda: _delete_confirm(claim_id, delete_dialog)
                            )
                
                delete_dialog.open()
            
            def _delete_confirm(claim_id: UUID, dialog) -> None:
                """Execute delete."""
                try:
                    claim = container.claim_repo.get_by_id(claim_id)
                    if not claim:
                        ui.notify("Gestión no encontrada", type="negative")
                        dialog.close()
                        return
                    
                    kind = container.claim_kind_repo.get_by_id(claim.claim_kind_id)
                    kind_name = kind.name if kind else "Unknown"
                    
                    if kind_name.upper() == "SOS":
                        container.eliminar_gestion_sos.execute(
                            EliminarGestionSOSInput(claim_id=claim_id)
                        )
                    else:
                        container.eliminar_grouped_claim.execute(
                            EliminarGroupedClaimInput(claim_id=claim_id)
                        )
                    
                    ui.notify("Gestión eliminada", type="positive")
                    _render_gestiones.refresh()
                except ClaimHasActivePaymentsError:
                    ui.notify("No se puede eliminar: hay pagos activos", type="negative")
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")
                finally:
                    dialog.close()

            # ── Gestiones table ───────────────────────────────────────────────

            @ui.refreshable
            def _render_gestiones() -> None:
                nonlocal _sort_col, _sort_dir, _page
                
                try:
                    # Prepare all data (O(N) pre-fetch with lookups)
                    all_prepared = _prepare_gestiones_data(container)
                    
                    if not all_prepared:
                        ui.label("No hay gestiones registradas").classes(
                            "text-gray-400 italic mt-4"
                        )
                        return
                    
                    # Apply filters from UI controls
                    filtered = _apply_filters_to_prepared_data(
                        all_prepared,
                        filter_kind=filter_kind.value,
                        filter_text=(filter_text.value or "").strip(),
                        filter_solved=filter_solved.value,
                        filter_has_payments=filter_has_payments.value,
                        filter_no_payments=filter_no_payments.value,
                        filter_has_nc=filter_has_nc.value,
                        filter_no_nc=filter_no_nc.value,
                        show_inactive=toggle.value,
                    )
                    
                    if not filtered:
                        ui.label("No hay gestiones que coincidan con los filtros").classes(
                            "text-gray-400 italic mt-4"
                        )
                        return
                    
                    # Apply sorting
                    sorted_data = _sort_prepared_data(filtered, _sort_col, _sort_dir)
                    
                    # Calculate pagination
                    total = len(sorted_data)
                    total_pages = max(1, math.ceil(total / _PAGE_SIZE))
                    if _page > total_pages:
                        _page = total_pages
                    page_start = (_page - 1) * _PAGE_SIZE
                    page_end = page_start + _PAGE_SIZE
                    page_data = sorted_data[page_start:page_end]
                    
                    # Render table with ui.table
                    table = ui.table(
                        columns=GESTIONES_COLUMNS,
                        rows=page_data,
                        row_key='id'
                    ).classes('w-full')
                    
                    # Add action icons as a table slot (Vue template)
                    table.add_slot('body-cell-acciones', '''
                        <q-td :props="props" class="text-center">
                            <q-btn icon="edit" @click="$parent.$emit('edit', props.row)" flat dense color="blue" size="sm" />
                            <q-btn icon="group" v-if="props.row.has_group" @click="$parent.$emit('grupo', props.row)" flat dense color="purple" size="sm" />
                            <q-btn icon="add_circle" v-if="!props.row.solved" @click="$parent.$emit('pagos', props.row)" flat dense color="green" size="sm" />
                            <q-btn icon="receipt" v-if="props.row.has_nc" @click="$parent.$emit('nc', props.row)" flat dense color="orange" size="sm" />
                            <q-btn icon="delete" @click="$parent.$emit('delete', props.row)" flat dense color="red" size="sm" />
                        </q-td>
                    ''')
                    
                    # Register event handlers for action buttons
                    def _handle_edit(row: dict) -> None:
                        claim_id = row.get('claim_id')
                        if claim_id:
                            ui.navigate.to(f'/gestiones/{claim_id}')
                    
                    def _handle_grupo(row: dict) -> None:
                        ui.notify("Grupo dialog - TBD", type="info")
                    
                    def _handle_pagos(row: dict) -> None:
                        ui.notify("Pagos dialog - TBD", type="info")
                    
                    def _handle_nc(row: dict) -> None:
                        ui.notify("NC dialog - TBD", type="info")
                    
                    def _handle_delete(row: dict) -> None:
                        claim_id = row.get('claim_id')
                        if claim_id:
                            _delete_gestion(claim_id)
                    
                    # Bind table events to handlers
                    table.on('edit', lambda e: _handle_edit(e.args))
                    table.on('grupo', lambda e: _handle_grupo(e.args))
                    table.on('pagos', lambda e: _handle_pagos(e.args))
                    table.on('nc', lambda e: _handle_nc(e.args))
                    table.on('delete', lambda e: _handle_delete(e.args))
                    
                    # Apply inactive row styling via CSS classes
                    # Note: Add data binding or CSS rule for inactive rows
                    if page_data:
                        for row in page_data:
                            if not row['active']:
                                # Could add CSS class via row styling if ui.table supports it
                                pass
                    
                    # Render pagination controls
                    with ui.row().classes("items-center justify-center gap-4 mt-4"):
                        with ui.row().classes("items-center gap-1"):
                            prev_btn = ui.button(
                                icon="chevron_left",
                                on_click=lambda: _go_to_page(_page - 1),
                            ).props("flat dense round")
                            if _page <= 1:
                                prev_btn.classes("opacity-30 pointer-events-none")

                            ui.label(f"Página {_page} de {total_pages}").classes(
                                "text-sm text-gray-300"
                            )

                            next_btn = ui.button(
                                icon="chevron_right",
                                on_click=lambda: _go_to_page(_page + 1),
                            ).props("flat dense round")
                            if _page >= total_pages:
                                next_btn.classes("opacity-30 pointer-events-none")

                        ui.label(f"({total} gestiones)").classes(
                            "text-xs text-gray-500"
                        )
                
                except Exception as e:
                    ui.notify(f"Error al cargar gestiones: {e}", type="negative")

            def _go_to_page(new_page: int) -> None:
                nonlocal _page
                _page = new_page
                _render_gestiones.refresh()

            # ── Initial render ─────────────────────────────────────────────────
            _render_gestiones()


def _get_kind_options(container: Container) -> dict[str, str]:
    try:
        kinds = container.obtener_claim_kinds.execute()
        return {k.name: k.name for k in kinds}
    except Exception:
        return {}
