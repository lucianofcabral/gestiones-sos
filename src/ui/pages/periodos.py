"""Periodos page — card-based view with invoices and NCs per period."""

from copy import deepcopy
from datetime import datetime
from uuid import UUID

from nicegui import ui

from src.domain.models.entities import Invoice, CreditNote
from src.infrastructure.container import Container
from src.ui.components.shell import AppShell
from src.ui.services.audit_helper import with_audit_user

_MESES_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def register_periodos_page() -> None:
    @ui.page("/periodos")
    def periodos_page() -> None:
        with AppShell():
            container = Container.get_instance()

            ui.label("Períodos").classes("text-2xl font-bold mb-4")

            @ui.refreshable
            def _render_periods() -> None:
                all_periods = container.listar_periodos.execute().periods

                # Only show current month and earlier
                now = datetime.now()
                current = now.year * 100 + now.month
                periods = [
                    p for p in all_periods
                    if p.year * 100 + p.month <= current
                ]
                periods.sort(key=lambda p: (p.year, p.month), reverse=True)

                if not periods:
                    ui.label("No hay períodos disponibles.").classes(
                        "text-gray-400 italic"
                    )
                    return

                for period in periods:
                    invoices = container.obtener_facturas.por_periodo(
                        period.period_id
                    )
                    ncs = container.obtener_ncs.get_by_period_id(period.period_id)

                    inv_active = [i for i in invoices if i.active]
                    nc_count = len(ncs)

                    _render_period_card(
                        period, invoices, ncs, _render_periods, container
                    )

            _render_periods()


def _render_period_card(
    period,
    invoices: list[Invoice],
    ncs: list[CreditNote],
    refresh_fn: callable,
    container: Container,
) -> None:
    """Render a single period as an expandable card with invoice/NC details."""
    total = sum(i.amount for i in invoices if i.active)
    nc_count = len(ncs)

    with ui.card().classes("w-full p-4 mb-4"):
        # ── Card header (clickable to expand) ──────────────────────────────
        expanded = {"value": False}

        with ui.row().classes(
            "items-center justify-between w-full cursor-pointer"
        ).on("click", lambda e, ex=expanded: ex.__setitem__("value", not ex["value"]) or _rebuild_detail(ex, detail_area, period, refresh_fn, container)):
            with ui.row().classes("items-center gap-4"):
                ui.icon("calendar_month", size="1.5rem")
                ui.label(period.period_name).classes("text-lg font-bold")
                ui.label(f"${total:,.2f}").classes("text-sm text-gray-400")

            with ui.row().classes("items-center gap-3"):
                ui.label(f"Facturas: {len(invoices)}").classes(
                    "text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full"
                )
                nc_label = (
                    f"NC: {nc_count}" if nc_count > 0 else "Sin NC"
                )
                nc_class = (
                    "bg-green-600 text-white" if nc_count > 0
                    else "bg-gray-600 text-white"
                )
                ui.label(nc_label).classes(
                    f"text-xs {nc_class} px-2 py-0.5 rounded-full"
                )

                ui.icon(
                    "expand_more" if not expanded["value"] else "expand_less",
                    size="1.5rem",
                )

        # ── Detail area (shown when expanded) ──────────────────────────────
        detail_area = ui.column().classes("w-full mt-4")
        detail_area.set_visibility(False)


def _rebuild_detail(
    expanded: dict,
    area: ui.column,
    period,
    refresh_fn: callable,
    container: Container,
) -> None:
    """Rebuild the detail section when toggling expansion."""
    area.clear()
    if not expanded["value"]:
        area.set_visibility(False)
        return

    area.set_visibility(True)
    invoices = container.obtener_facturas.por_periodo(period.period_id)
    ncs = container.obtener_ncs.get_by_period_id(period.period_id)

    with area:
        # ── Invoices section ───────────────────────────────────────────────
        with ui.row().classes("items-center justify-between"):
            ui.label("Facturas").classes("text-md font-bold")
            ui.button(
                "Agregar Factura",
                icon="add",
                on_click=lambda: _invoice_dialog(
                    None, period, refresh_fn, container,
                ),
            ).props("flat size=sm color=white")

        if invoices:
            # Define table columns
            table_columns = [
                {'name': 'numero', 'label': 'Número', 'field': 'numero', 'align': 'left', 'sortable': True},
                {'name': 'fecha', 'label': 'Fecha', 'field': 'fecha', 'align': 'left', 'sortable': True},
                {'name': 'importe', 'label': 'Importe', 'field': 'importe', 'align': 'right', 'sortable': True},
                {'name': 'descripcion', 'label': 'Descripción', 'field': 'descripcion', 'align': 'left', 'sortable': True},
                {'name': 'activo', 'label': 'Activo', 'field': 'activo', 'align': 'center', 'sortable': True},
                {'name': 'acciones', 'label': 'Acciones', 'field': 'acciones', 'align': 'center', 'sortable': False},
            ]
            
            # Prepare table data
            table_rows = []
            for inv in invoices:
                table_rows.append({
                    'id': str(inv.invoice_id),
                    'invoice_id': inv.invoice_id,
                    'numero': inv.invoice_number,
                    'fecha': inv.emited_date.strftime('%Y-%m-%d'),
                    'importe': f'${inv.amount:,.2f}',
                    'descripcion': inv.description or '—',
                    'activo': 'Sí' if inv.active else 'No',
                    'active': inv.active,
                })
            
            # Create table
            table = ui.table(columns=table_columns, rows=table_rows, row_key='id').classes('w-full')
            
            # Add action buttons slot
            table.add_slot('body-cell-acciones', '''
                <q-td :props="props" class="text-center">
                    <q-btn icon="edit" @click="$parent.$emit('edit', props.row)" flat dense color="blue" size="sm" />
                    <q-btn :icon="props.row.active ? 'toggle_off' : 'toggle_on'" @click="$parent.$emit('toggle', props.row)" flat dense :color="props.row.active ? 'green' : 'red'" size="sm" />
                </q-td>
            ''')
            
            # Register event handlers
            def _handle_edit_inv(row: dict) -> None:
                inv_id = row.get('invoice_id')
                if inv_id:
                    inv = container.billing_repo.get_by_id(inv_id)
                    if inv:
                        with ui.dialog() as edit_dlg:
                            _invoice_dialog(inv, period, refresh_fn, container, edit_dlg)
                        edit_dlg.open()
            
            def _handle_toggle_inv(row: dict) -> None:
                inv_id = row.get('invoice_id')
                if inv_id:
                    ui.notify(f"Toggle {inv_id} - TBD", type="info")
            
            table.on('edit', lambda e: _handle_edit_inv(e.args))
            table.on('toggle', lambda e: _handle_toggle_inv(e.args))
        else:
            ui.label("No hay facturas en este período.").classes(
                "text-sm text-gray-400 italic"
            )

        ui.separator().classes("my-4")

        # ── NC section ────────────────────────────────────────────────────
        ui.label("Notas de Crédito").classes("text-md font-bold mb-2")

        if ncs:
            # Define table columns for NC
            nc_columns = [
                {'name': 'pago_id', 'label': 'ID Pago', 'field': 'pago_id', 'align': 'left', 'sortable': True},
                {'name': 'entregado', 'label': 'Entregado', 'field': 'entregado', 'align': 'center', 'sortable': True},
                {'name': 'fecha', 'label': 'Fecha', 'field': 'fecha', 'align': 'left', 'sortable': True},
                {'name': 'acciones', 'label': 'Acciones', 'field': 'acciones', 'align': 'center', 'sortable': False},
            ]
            
            # Prepare table data
            nc_rows = []
            for nc in ncs:
                nc_rows.append({
                    'id': str(nc.nc_payment_id),
                    'nc_payment_id': nc.nc_payment_id,
                    'pago_id': str(nc.payment_id)[:8] + '...',
                    'entregado': 'Sí' if nc.delivered else 'No',
                    'delivered': nc.delivered,
                    'fecha': nc.created_date.strftime('%Y-%m-%d'),
                })
            
            # Create table
            nc_table = ui.table(columns=nc_columns, rows=nc_rows, row_key='id').classes('w-full')
            
            # Add action buttons slot
            nc_table.add_slot('body-cell-acciones', '''
                <q-td :props="props" class="text-center">
                    <q-btn icon="link_off" @click="$parent.$emit('disassociate', props.row)" flat dense color="orange" size="sm" />
                </q-td>
            ''')
            
            # Register event handler
            def _handle_disassociate_nc(row: dict) -> None:
                nc_id = row.get('nc_payment_id')
                if nc_id:
                    _disassociate_nc(nc_id, refresh_fn, container)
            
            nc_table.on('disassociate', lambda e: _handle_disassociate_nc(e.args))
        else:
            ui.label("No hay notas de crédito en este período.").classes(
                "text-sm text-gray-400 italic"
            )


def _toggle_invoice(
    invoice_id: UUID, active: bool, refresh_fn: callable, container: Container,
) -> None:
    if active:
        container.billing_repo.activate(invoice_id)
    else:
        container.billing_repo.inactivate(invoice_id)
    ui.notify(
        "Factura activada" if active else "Factura inactivada",
        type="positive",
    )
    refresh_fn()


@with_audit_user
def _disassociate_nc(
    nc_id: UUID, refresh_fn: callable, container: Container,
) -> None:
    try:
        nc = container.obtener_ncs.get_by_id(nc_id)
        if not nc:
            ui.notify("Nota de crédito no encontrada", type="warning")
            return
        updated = deepcopy(nc)
        updated.period_id = None
        container.nc_payment_repo.update(nc_id, updated)
        ui.notify("Nota de crédito desvinculada del período", type="positive")
        refresh_fn()
    except Exception as e:
        ui.notify(f"Error: {e}", type="negative")


# ── Invoice Dialog (reused from facturacion, adapted for period context) ────────


def _invoice_dialog(
    invoice: Invoice | None,
    period,
    refresh_fn: callable,
    container: Container,
    existing_dialog: ui.dialog | None = None,
) -> None:
    is_edit = invoice is not None

    if existing_dialog:
        _render_form(existing_dialog, invoice, period, refresh_fn, container)
    else:
        with ui.dialog() as dlg, ui.card().classes("w-[400px] max-w-full"):
            _render_form(dlg, invoice, period, refresh_fn, container)
        dlg.open()


def _render_form(
    dlg: ui.dialog,
    invoice: Invoice | None,
    period,
    refresh_fn: callable,
    container: Container,
) -> None:
    is_edit = invoice is not None
    ui.label("Editar Factura" if is_edit else "Nueva Factura").classes(
        "text-lg font-bold mb-2"
    )

    num_input = ui.input(
        label="Número de factura",
        value=invoice.invoice_number if invoice else "",
    ).classes("w-full")

    date_input = ui.input(
        label="Fecha de emisión",
        placeholder="YYYY-MM-DD",
        value=invoice.emited_date.strftime("%Y-%m-%d") if invoice else "",
    ).classes("w-full")

    amount_input = ui.number(
        label="Monto",
        value=invoice.amount if invoice else 0,
        precision=2,
    ).classes("w-full")

    desc_input = ui.textarea(
        label="Descripción",
        value=invoice.description or "" if invoice else "",
    ).classes("w-full")

    with ui.row().classes("gap-2 justify-end mt-2"):
        ui.button("Cancelar", on_click=dlg.close).props("flat")

        @with_audit_user
        async def _save() -> None:
            num = (num_input.value or "").strip()
            date_str = (date_input.value or "").strip()
            amount = amount_input.value
            desc = (desc_input.value or "").strip() or None

            missing = []
            if not num:
                missing.append("Número")
            if not date_str:
                missing.append("Fecha")
            if not amount or float(amount) <= 0:
                missing.append("Monto")
            if missing:
                ui.notify(
                    "Campos requeridos: " + ", ".join(missing), type="warning",
                )
                return

            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                ui.notify("Fecha inválida. Use YYYY-MM-DD", type="warning")
                return

            try:
                if is_edit and invoice:
                    kwargs = {"invoice_number": num}
                    for f in ("invoice_id", "period_id", "created_at", "active"):
                        kwargs[f] = deepcopy(getattr(invoice, f))
                    kwargs["period_id"] = period.period_id
                    kwargs["emited_date"] = parsed_date
                    kwargs["amount"] = float(amount)
                    kwargs["description"] = desc
                    updated = Invoice(**kwargs)
                    container.billing_repo.update(invoice.invoice_id, updated)
                    ui.notify("Factura actualizada", type="positive")
                else:
                    inp = container.registrar_factura.Input(
                        invoice_number=num,
                        period_id=period.period_id,
                        emited_date=parsed_date,
                        amount=float(amount),
                        description=desc,
                    )
                    container.registrar_factura.execute(inp)
                    ui.notify("Factura registrada", type="positive")
            except Exception as e:
                ui.notify(f"Error: {e}", type="negative")
                return

            dlg.close()
            refresh_fn()
