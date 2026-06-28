"""Pagos page — CRUD for payments with filters and NC management."""

from datetime import datetime
from uuid import UUID

from nicegui import ui

from src.application.use_cases.payments.actualizar_pago import (
    ActualizarPagoInput,
)
from src.application.use_cases.payments.inactivar_pago import (
    InactivarPagoInput,
)
from src.application.use_cases.payments.activar_pago import ActivarPagoInput
from src.application.use_cases.payments.registrar_pago import (
    RegistrarPagoInput,
)
from src.infrastructure.container import Container
from src.ui.components.shell import AppShell
from src.ui.services.audit_helper import with_audit_user


def _prepare_pagos_data(container: Container) -> list[dict]:
    """
    Prepare pagos table data by pre-computing all lookups in one pass.
    
    Returns list of dicts with fields:
        id, payment_id, monto, pagador, medio, beneficiario, cliente, tipo,
        grupo, dominio, poliza, gestion, fecha, nc, activo
    
    Complexity: O(N) where N = number of payments.
    """
    # Fetch all payments
    all_payments = container.payment_repo.get_all()
    if not all_payments:
        return []
    
    # Pre-fetch lookups
    all_agents = {str(a.agent_id): a.name for a in container.agent_repo.get_all()}
    all_vias = {str(v.payment_via_id): v.name for v in container.payment_via_repo.get_all()}
    all_claims = {c.claim_id: c for c in container.claim_repo.get_all()}
    all_kinds = {k.claim_kind_id: k.name for k in container.claim_kind_repo.get_all()}
    
    # Pre-compute groups
    all_groups = {}
    for gc in container.group_claim_repo.get_all():
        grp = container.obtener_grupo.execute(
            type('Input', (), {'group_id': gc.group_claim_id})()
        )
        if grp:
            all_groups[gc.claim_id] = grp.name
    
    # Pre-compute NC status per payment
    nc_status = {}
    for p in all_payments:
        nc = container.obtener_ncs.get_by_payment_id(p.payment_id)
        nc_status[p.payment_id] = (
            "Entregado" if nc and nc.delivered
            else "Pendiente" if nc
            else "—"
        )
    
    # Build rows
    rows = []
    for p in all_payments:
        claim = all_claims.get(p.claim_id)
        
        row = {
            'id': str(p.payment_id),
            'payment_id': p.payment_id,
            'monto': f'${p.amount:,.2f}',
            'pagador': all_agents.get(str(p.payer_id), '—'),
            'medio': all_vias.get(str(p.payment_via_id), '—'),
            'beneficiario': all_agents.get(str(p.payee_id), '—'),
            'cliente': claim.claimer_name if claim else '—',
            'tipo': all_kinds.get(claim.claim_kind_id, '—') if claim else '—',
            'grupo': all_groups.get(p.claim_id, '—'),
            'dominio': claim.plate if claim else '—',
            'poliza': claim.policy_number if claim else '—',
            'gestion': str(p.claim_id),
            'fecha': p.created_date.strftime('%d/%m/%Y'),
            'nc': nc_status[p.payment_id],
            'activo': p.active,
        }
        rows.append(row)
    
    return rows


# ── Table Column Definitions ────────────────────────────────────────

PAGOS_COLUMNS = [
    {
        'name': 'monto',
        'label': 'Monto',
        'field': 'monto',
        'align': 'right',
        'sortable': True,
        'style': 'min-width: 112px;'
    },
    {
        'name': 'pagador',
        'label': 'Pagador',
        'field': 'pagador',
        'align': 'left',
        'sortable': True,
        'style': 'min-width: 112px;'
    },
    {
        'name': 'medio',
        'label': 'Medio',
        'field': 'medio',
        'align': 'left',
        'sortable': True,
        'style': 'min-width: 96px;'
    },
    {
        'name': 'beneficiario',
        'label': 'Beneficiario',
        'field': 'beneficiario',
        'align': 'left',
        'sortable': True,
        'style': 'min-width: 112px;'
    },
    {
        'name': 'cliente',
        'label': 'Cliente',
        'field': 'cliente',
        'align': 'left',
        'sortable': True,
        'style': 'flex: 1; min-width: 170px;'
    },
    {
        'name': 'tipo',
        'label': 'Tipo',
        'field': 'tipo',
        'align': 'left',
        'sortable': True,
        'style': 'min-width: 96px;'
    },
    {
        'name': 'grupo',
        'label': 'Grupo',
        'field': 'grupo',
        'align': 'left',
        'sortable': True,
        'style': 'min-width: 96px;'
    },
    {
        'name': 'dominio',
        'label': 'Dominio',
        'field': 'dominio',
        'align': 'left',
        'sortable': True,
        'style': 'min-width: 96px;'
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
        'name': 'gestion',
        'label': 'Gestión',
        'field': 'gestion',
        'align': 'left',
        'sortable': True,
        'style': 'min-width: 96px;'
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
        'name': 'nc',
        'label': 'NC',
        'field': 'nc',
        'align': 'center',
        'sortable': True,
        'style': 'min-width: 96px;'
    },
    {
        'name': 'activo',
        'label': 'Activo',
        'field': 'activo',
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


def _render_pagos_actions(payment_id: UUID, row_data: dict) -> None:
    """
    Render action icons for a pagos row.
    
    Args:
        payment_id: UUID of the payment
        row_data: Dict with keys: activo, nc
    """
    from src.ui.components.table_helpers import ActionButton
    
    with ui.row().classes("gap-1 items-center no-wrap"):
        # Edit icon (always visible)
        ActionButton(
            icon='edit',
            label='Editar',
            on_click=lambda: ui.notify("Edit payment dialog - TBD", type="warning"),
            color='text-blue-500'
        )
        
        # Toggle active/inactive icon
        if row_data.get('activo'):
            ActionButton(
                icon='toggle_on',
                label='Desactivar',
                on_click=lambda: ui.notify("Deactivate payment - TBD", type="warning"),
                color='text-green-500'
            )
        else:
            ActionButton(
                icon='toggle_off',
                label='Activar',
                on_click=lambda: ui.notify("Activate payment - TBD", type="warning"),
                color='text-gray-500'
            )
        
        # View NC icon (conditional: only if NC exists)
        if row_data.get('nc') and row_data.get('nc') != '—':
            ActionButton(
                icon='receipt',
                label='Ver Crédito',
                on_click=lambda: ui.notify("View NC dialog - TBD", type="warning"),
                color='text-orange-500'
            )


def register_pagos_page() -> None:
    @ui.page("/pagos")
    def pagos_page() -> None:
        with AppShell():
            container = Container.get_instance()

            # ── Header ────────────────────────────────────────────────────────
            with ui.row().classes("items-center gap-2"):
                ui.label("Pagos").classes("text-2xl font-bold")
                ui.label("— Administración de pagos").classes(
                    "text-sm text-gray-400 self-end mb-1"
                )

            # ── Helper data fetchers ──────────────────────────────────────────
            def _get_agent_options() -> dict[str, str]:
                agents = container.agent_repo.get_all()
                return {str(a.agent_id): a.name for a in agents}

            def _get_via_options() -> dict[str, str]:
                vias = container.payment_via_repo.get_all()
                return {str(v.payment_via_id): v.name for v in vias}

            def _get_period_options() -> dict[str, str]:
                result = container.listar_periodos.execute()
                return {str(p.period_id): p.period_name for p in result.periods}

            # Cache options for dialogs (refreshed each page load)
            _cached_agent_options = _get_agent_options()
            _cached_via_options = _get_via_options()

            # ── Filter state ──────────────────────────────────────────────────
            filter_claim_id = (
                ui.input(label="Nº Gestión", placeholder="ID exacto...")
                .props("dense outlined")
                .classes("w-40")
            )
            filter_date_from = (
                ui.input(label="Fecha desde", placeholder="YYYY-MM-DD")
                .props("dense outlined")
                .classes("w-36")
            )
            filter_date_to = (
                ui.input(label="Fecha hasta", placeholder="YYYY-MM-DD")
                .props("dense outlined")
                .classes("w-36")
            )
            filter_amount_min = (
                ui.number(label="Monto mín", precision=2)
                .props("dense outlined")
                .classes("w-32")
            )
            filter_amount_max = (
                ui.number(label="Monto máx", precision=2)
                .props("dense outlined")
                .classes("w-32")
            )
            filter_active_only = ui.checkbox("Solo activos")

            # ── Text filter (live, searches claim fields) ─────────────────────
            filter_text = (
                ui.input(
                    label="Buscar",
                    placeholder="Póliza, cliente o dominio...",
                )
                .props("dense outlined")
                .classes("w-64")
                .on("update:model-value", lambda: _payments_table.refresh())
            )

            # ── Action + Filter row ───────────────────────────────────────────
            with ui.row().classes("items-center gap-2 mt-2 flex-wrap"):
                ui.button(
                    "Nuevo Pago",
                    icon="add",
                    on_click=lambda: _open_create_dialog(),
                )
                ui.button(
                    "Aplicar Filtros",
                    icon="search",
                    on_click=lambda: _payments_table.refresh(),
                )
                ui.button(
                    "Limpiar Filtros",
                    icon="clear",
                    on_click=lambda: _clear_filters(),
                )

            ui.separator().classes("my-2")

            # ── Filter logic (client-side) ────────────────────────────────────
            def _apply_filters(payments: list) -> list:
                cid = (filter_claim_id.value or "").strip().lower()
                dfrom = (filter_date_from.value or "").strip()
                dto = (filter_date_to.value or "").strip()
                amin = filter_amount_min.value
                amax = filter_amount_max.value
                active_only = filter_active_only.value

                result = payments

                if cid:
                    result = [
                        p
                        for p in result
                        if cid in str(p.claim_id).lower()
                    ]

                if dfrom:
                    try:
                        fd = datetime.strptime(dfrom, "%Y-%m-%d").date()
                        result = [
                            p for p in result if p.created_date.date() >= fd
                        ]
                    except ValueError:
                        pass

                if dto:
                    try:
                        td = datetime.strptime(dto, "%Y-%m-%d").date()
                        result = [
                            p for p in result if p.created_date.date() <= td
                        ]
                    except ValueError:
                        pass

                if amin is not None:
                    try:
                        result = [
                            p for p in result if p.amount >= float(amin)
                        ]
                    except (ValueError, TypeError):
                        pass

                if amax is not None:
                    try:
                        result = [
                            p for p in result if p.amount <= float(amax)
                        ]
                    except (ValueError, TypeError):
                        pass

                if active_only:
                    result = [p for p in result if p.active]

                return result

            def _clear_filters() -> None:
                filter_claim_id.value = ""
                filter_text.value = ""
                filter_date_from.value = ""
                filter_date_to.value = ""
                filter_amount_min.value = None
                filter_amount_max.value = None
                filter_active_only.value = False
                _payments_table.refresh()

            # ── NC helper: see if a payment has a linked NC ───────────────────
            def _payment_has_nc(payment_id: UUID) -> bool:
                nc = container.obtener_ncs.get_by_payment_id(payment_id)
                return nc is not None

            # ── Sort state ────────────────────────────────────────────────────
            _sort_col = 0
            _sort_dir = 1

            def _sort(col_idx: int) -> None:
                nonlocal _sort_col, _sort_dir
                if _sort_col == col_idx:
                    _sort_dir *= -1
                else:
                    _sort_col = col_idx
                    _sort_dir = 1
                _payments_table.refresh()

            # ── Payments table (refreshable) ──────────────────────────────────
            @ui.refreshable
            def _payments_table() -> None:
                nonlocal _sort_col, _sort_dir
                all_payments = container.obtener_pagos.get_all()
                payments = _apply_filters(all_payments)

                if not payments:
                    ui.label("No hay pagos registrados").classes(
                        "text-gray-400 italic mt-4"
                    )
                    return

                # Resolve agent names + via names for the current set
                agent_options = _get_agent_options()
                via_options = _get_via_options()

                # Resolve claim data for all payments
                all_claims = {
                    c.claim_id: c for c in container.claim_repo.get_all()
                }
                all_kinds = {
                    k.claim_kind_id: k.name
                    for k in container.claim_kind_repo.get_all()
                }
                all_groups: dict[UUID, str] = {}
                for gc in container.grouped_claim_repo.get_all():
                    grp = container.group_claim_repo.get_by_id(
                        gc.group_claim_id
                    )
                    if grp:
                        all_groups[gc.claim_id] = grp.name

                # Pre-compute NC status per payment
                nc_status: dict[UUID, str] = {}
                for p in payments:
                    nc = container.obtener_ncs.get_by_payment_id(p.payment_id)
                    nc_status[p.payment_id] = (
                        "Entregado" if nc and nc.delivered
                        else "Pendiente" if nc
                        else ""
                    )

                # ── Text filter (on claim fields: policy, customer, plate) ─
                q = (filter_text.value or "").strip().lower()
                if q:
                    filtered: list = []
                    for p in payments:
                        claim = all_claims.get(p.claim_id)
                        if not claim:
                            filtered.append(p)
                            continue
                        if (
                            q in claim.policy_number.lower()
                            or q in claim.claimer_name.lower()
                            or q in claim.plate.lower()
                        ):
                            filtered.append(p)
                    payments = filtered

                if not payments:
                    ui.label(
                        "No hay pagos que coincidan con los filtros"
                    ).classes("text-gray-400 italic mt-4")
                    return

                # Sort
                _sort_keys = [
                    lambda p: p.amount,
                    lambda p: agent_options.get(str(p.payer_id), ""),
                    lambda p: via_options.get(str(p.payment_via_id), ""),
                    lambda p: agent_options.get(str(p.payee_id), ""),
                    lambda p: all_claims.get(p.claim_id).claimer_name if all_claims.get(p.claim_id) else "",
                    lambda p: all_kinds.get(all_claims[p.claim_id].claim_kind_id, "") if p.claim_id in all_claims else "",
                    lambda p: all_groups.get(p.claim_id, ""),
                    lambda p: all_claims.get(p.claim_id).plate if all_claims.get(p.claim_id) else "",
                    lambda p: all_claims.get(p.claim_id).policy_number if all_claims.get(p.claim_id) else "",
                    lambda p: str(p.claim_id),
                    lambda p: p.created_date,
                    lambda p: nc_status.get(p.payment_id, ""),
                    lambda p: p.active,
                ]
                payments = sorted(
                    payments, key=_sort_keys[_sort_col],
                    reverse=_sort_dir == -1
                )

                # Header
                _cols = [
                    ("Monto", "w-24 text-right"),
                    ("Pagador", "w-24"),
                    ("Medio", "w-20"),
                    ("Beneficiario", "w-24"),
                    ("Cliente", "w-28"),
                    ("Tipo", "w-20"),
                    ("Grupo", "w-20"),
                    ("Dominio", "w-24"),
                    ("Póliza", "w-24"),
                    ("Gestión", "w-20"),
                    ("Fecha", "w-24"),
                    ("NC", "w-20"),
                    ("Activo", "w-14"),
                    ("Acciones", "w-36"),
                ]
                with ui.row().classes(
                    "items-center gap-2 py-2 border-b border-gray-600 font-bold"
                ):
                    for i, (label, width) in enumerate(_cols):
                        arrow = (
                            " ▲" if _sort_col == i and _sort_dir == 1
                            else " ▼" if _sort_col == i
                            else ""
                        )
                        ui.label(f"{label}{arrow}").classes(
                            f"text-xs {width} cursor-pointer"
                        ).on("click", lambda i=i: _sort(i))

                # Rows
                for p in payments:
                    payer_name = agent_options.get(str(p.payer_id), "—")
                    payee_name = agent_options.get(str(p.payee_id), "—")
                    via_name = via_options.get(str(p.payment_via_id), "—")

                    # Resolve claim data
                    claim = all_claims.get(p.claim_id)
                    c_name = claim.claimer_name if claim else "—"
                    c_kind = (
                        all_kinds.get(claim.claim_kind_id, "—")
                        if claim
                        else "—"
                    )
                    c_group = (
                        all_groups.get(claim.claim_id, "—")
                        if claim
                        else "—"
                    )
                    c_plate = claim.plate if claim else "—"
                    c_policy = claim.policy_number if claim else "—"

                    # Check NC status for this payment
                    nc = container.obtener_ncs.get_by_payment_id(p.payment_id)
                    nc_badge = ""
                    nc_color = ""
                    if nc is not None:
                        if nc.delivered:
                            nc_badge = "Entregado"
                            nc_color = "bg-green-600"
                        else:
                            nc_badge = "Pendiente"
                            nc_color = "bg-yellow-600"
                    else:
                        nc_badge = "—"
                        nc_color = "bg-gray-600"

                    with ui.row().classes(
                        "items-center gap-2 py-1 hover:bg-gray-800"
                    ):
                        ui.label(f"${p.amount:,.2f}").classes(
                            "text-sm w-24 text-right"
                        )
                        ui.label(payer_name).classes("text-sm w-24")
                        ui.label(via_name).classes("text-sm w-20")
                        ui.label(payee_name).classes("text-sm w-24")
                        ui.label(c_name).classes("text-sm w-28")
                        ui.label(c_kind).classes("text-sm w-20")
                        ui.label(c_group).classes("text-sm w-20")
                        ui.label(c_plate).classes("text-sm w-24")
                        ui.label(c_policy).classes("text-sm w-24")
                        ui.label(str(p.claim_id)[:8]).classes(
                            "text-sm w-20 text-gray-400"
                        )
                        ui.label(
                            p.created_date.strftime("%Y-%m-%d")
                        ).classes("text-sm w-24 text-gray-400")

                        # NC badge
                        ui.label(nc_badge).classes(
                            f"text-xs font-bold px-2 py-0.5 rounded-full "
                            f"{nc_color} text-white w-20 text-center"
                        )

                        # Active badge
                        badge_color = (
                            "bg-green-600" if p.active else "bg-red-600"
                        )
                        ui.label("Sí" if p.active else "No").classes(
                            f"text-xs font-bold px-2 py-0.5 rounded-full "
                            f"{badge_color} text-white w-14 text-center"
                        )

                        # ── Action buttons ────────────────────────────────
                        with ui.row().classes("gap-1 w-36"):
                            # Edit
                            with ui.dialog() as edit_dialog:
                                _edit_payment_dialog(
                                    edit_dialog, p, agent_options,
                                    via_options, _payments_table,
                                )
                            ui.button(
                                icon="edit",
                                on_click=edit_dialog.open,
                            ).props("flat dense round size=sm")

                            # Inactivate / Activate
                            with ui.dialog() as confirm_dialog:
                                _confirm_toggle_active(
                                    confirm_dialog, p, _payments_table,
                                )

                            async def _toggle_click(
                                pid: UUID = p.payment_id,
                                active: bool = p.active,
                                dlg=confirm_dialog,
                            ) -> None:
                                if active:
                                    res = container.can_inactivate_svc.execute(
                                        pid
                                    )
                                    can, reason = res
                                    if not can:
                                        ui.notify(reason, type="warning")
                                        return
                                    dlg._reason = reason
                                    dlg._is_activate = False
                                else:
                                    payment = (
                                        container.obtener_pagos.get_by_id(pid)
                                    )
                                    if payment is None:
                                        ui.notify(
                                            "Pago no encontrado",
                                            type="negative",
                                        )
                                        return
                                    res = container.can_activate_svc.execute(
                                        payment
                                    )
                                    can, reason = res
                                    if not can:
                                        ui.notify(reason, type="warning")
                                        return
                                    dlg._reason = reason
                                    dlg._is_activate = True
                                dlg.open()

                            ui.button(
                                icon="toggle_off"
                                if p.active
                                else "toggle_on",
                                on_click=_toggle_click,
                            ).props("flat dense round size=sm")

            # ══════════════════════════════════════════════════════════════════
            # DIALOG DEFINITIONS
            # ══════════════════════════════════════════════════════════════════

            # ── Create Payment Dialog ─────────────────────────────────────────
            def _open_create_dialog() -> None:
                """Open the create payment dialog with fresh form."""
                agent_options = _get_agent_options()
                via_options = _get_via_options()

                with ui.dialog() as dlg, ui.card():
                    ui.label("Nuevo Pago").classes("text-lg font-bold mb-2")

                    cid_input = ui.input(
                        label="ID de Gestión",
                        placeholder="UUID de la gestión...",
                    )
                    payer_select = ui.select(
                        label="Pagador",
                        options=agent_options,
                        with_input=True,
                    ).classes("w-full")
                    payee_select = ui.select(
                        label="Beneficiario",
                        options=agent_options,
                        with_input=True,
                    ).classes("w-full")
                    via_select = ui.select(
                        label="Medio de Pago",
                        options=via_options,
                        with_input=True,
                    ).classes("w-full")
                    amount_input = ui.number(
                        label="Monto",
                        precision=2,
                    )

                    # Submit / Cancel
                    with ui.row().classes("gap-2 justify-end mt-2"):
                        ui.button("Cancelar", on_click=dlg.close).props("flat")

                        @with_audit_user
                        async def _save() -> None:
                            # Validate required fields
                            missing = []
                            cid_val = (cid_input.value or "").strip()
                            payer_val = payer_select.value
                            payee_val = payee_select.value
                            via_val = via_select.value
                            amount_val = amount_input.value

                            if not cid_val:
                                missing.append("ID de Gestión")
                            if not payer_val:
                                missing.append("Pagador")
                            if not payee_val:
                                missing.append("Beneficiario")
                            if not via_val:
                                missing.append("Medio de Pago")
                            if not amount_val or float(amount_val) <= 0:
                                missing.append("Monto")

                            if missing:
                                ui.notify(
                                    "Campos requeridos: "
                                    + ", ".join(missing),
                                    type="warning",
                                )
                                return

                            try:
                                inp = RegistrarPagoInput(
                                    claim_id=UUID(cid_val),
                                    payer_id=UUID(payer_val),
                                    payee_id=UUID(payee_val),
                                    payment_via_id=UUID(via_val),
                                    amount=float(amount_val),
                                )
                                container.registrar_pago.execute(inp)
                                ui.notify(
                                    "Pago registrado", type="positive"
                                )
                                dlg.close()
                                _payments_table.refresh()
                            except ValueError as e:
                                ui.notify(str(e), type="negative")
                            except Exception as e:
                                ui.notify(
                                    f"Error al registrar pago: {e}",
                                    type="negative",
                                )

                        ui.button("Guardar", on_click=_save)

                dlg.open()

            # ── Edit Payment Dialog (per row) ────────────────────────────────
            def _edit_payment_dialog(
                dialog: ui.dialog,
                payment,
                agent_options: dict,
                via_options: dict,
                refresh_fn,
            ) -> None:
                """Render edit dialog content for a single payment."""
                has_nc = _payment_has_nc(payment.payment_id)

                with dialog, ui.card():
                    ui.label("Editar Pago").classes("text-lg font-bold mb-2")

                    if has_nc:
                        ui.label(
                            "Solo el monto puede modificarse cuando existe "
                            "una Nota de Crédito asociada."
                        ).classes("text-xs text-yellow-400 mb-2")

                    cid_input = ui.input(
                        label="ID de Gestión",
                        value=str(payment.claim_id),
                    )
                    cid_input.set_enabled(False)

                    payer_select = ui.select(
                        label="Pagador",
                        options=agent_options,
                        value=str(payment.payer_id),
                        with_input=True,
                    ).classes("w-full")
                    if has_nc:
                        payer_select.set_enabled(False)

                    payee_select = ui.select(
                        label="Beneficiario",
                        options=agent_options,
                        value=str(payment.payee_id),
                        with_input=True,
                    ).classes("w-full")
                    if has_nc:
                        payee_select.set_enabled(False)

                    via_select = ui.select(
                        label="Medio de Pago",
                        options=via_options,
                        value=str(payment.payment_via_id),
                        with_input=True,
                    ).classes("w-full")
                    if has_nc:
                        via_select.set_enabled(False)

                    amount_input = ui.number(
                        label="Monto",
                        value=payment.amount,
                        precision=2,
                    )

                    with ui.row().classes("gap-2 justify-end mt-2"):
                        ui.button("Cancelar", on_click=dialog.close).props(
                            "flat"
                        )

                        @with_audit_user
                        async def _save() -> None:
                            payer_val = payer_select.value
                            payee_val = payee_select.value
                            via_val = via_select.value
                            amount_val = amount_input.value

                            if not amount_val or float(amount_val) <= 0:
                                ui.notify(
                                    "El monto debe ser mayor a cero",
                                    type="warning",
                                )
                                return

                            try:
                                kwargs: dict = {
                                    "payment_id": payment.payment_id,
                                }
                                if not has_nc:
                                    if payer_val:
                                        kwargs["payer_id"] = UUID(payer_val)
                                    if payee_val:
                                        kwargs["payee_id"] = UUID(payee_val)
                                    if via_val:
                                        kwargs["payment_via_id"] = UUID(
                                            via_val
                                        )
                                if amount_val is not None:
                                    kwargs["amount"] = float(amount_val)

                                inp = ActualizarPagoInput(**kwargs)
                                result = container.actualizar_pago.execute(
                                    inp
                                )
                                if not result.success:
                                    ui.notify(
                                        "Pago no encontrado",
                                        type="negative",
                                    )
                                    dialog.close()
                                    return

                                dialog.close()
                                ui.notify(
                                    "Pago actualizado", type="positive"
                                )
                                refresh_fn.refresh()
                            except ValueError as e:
                                ui.notify(str(e), type="negative")
                            except Exception as e:
                                ui.notify(
                                    f"Error al actualizar pago: {e}",
                                    type="negative",
                                )

                        ui.button("Guardar", on_click=_save)

            # ── Confirm Inactivate / Activate Dialog (per row) ───────────────
            def _confirm_toggle_active(
                dialog: ui.dialog,
                payment,
                refresh_fn,
            ) -> None:
                """Render confirmation dialog for inactivate/activate."""
                is_activate = not payment.active
                action_label = "Activar" if is_activate else "Inactivar"

                with dialog, ui.card():
                    ui.label(
                        f"¿{action_label} pago?"
                    ).classes("text-lg font-bold")
                    ui.label(
                        f"¿Está seguro de {action_label.lower()} "
                        f"el pago por ${payment.amount:,.2f}?"
                    )

                    reason_label = ui.label("").classes(
                        "text-sm text-gray-400 mt-1"
                    )

                    def _set_reason(reason_text: str) -> None:
                        reason_label.text = f"Motivo: {reason_text}"

                    dialog._reason = ""
                    dialog._is_activate = is_activate

                    with ui.row().classes("gap-2 justify-end mt-2"):
                        ui.button("Cancelar", on_click=dialog.close).props(
                            "flat"
                        )

                        @with_audit_user
                        async def _confirm() -> None:
                            try:
                                if dialog._is_activate:
                                    inp = ActivarPagoInput(
                                        payment_id=payment.payment_id
                                    )
                                    result = container.activar_pago.execute(
                                        inp
                                    )
                                else:
                                    inp = InactivarPagoInput(
                                        payment_id=payment.payment_id
                                    )
                                    result = (
                                        container.inactivar_pago.execute(inp)
                                    )

                                if result.success:
                                    ui.notify(
                                        result.reason, type="positive"
                                    )
                                else:
                                    ui.notify(
                                        result.reason, type="warning"
                                    )

                                dialog.close()
                                refresh_fn.refresh()
                            except Exception as e:
                                ui.notify(str(e), type="negative")
                                dialog.close()

                        ui.button(
                            action_label,
                            on_click=_confirm,
                        )

            # Initial render — dialog definitions must precede this call
            _payments_table()


# ── Shared helpers ─────────────────────────────────────────────────────────


def _nc_field(label: str, value: str) -> None:
    """Render a labeled field inside an NC detail grid."""
    with ui.column().classes("gap-0"):
        ui.label(label).classes("text-xs text-gray-400")
        ui.label(value).classes("text-sm")
