"""Facturación page — invoice list with filters, inline toggle, and create/edit dialog."""

from copy import deepcopy
from datetime import datetime
from uuid import UUID

from nicegui import ui

from src.domain.models.entities import Invoice
from src.infrastructure.container import Container
from src.ui.components.shell import AppShell
from src.ui.services.audit_helper import with_audit_user


def register_facturacion_page() -> None:
    @ui.page("/facturas")
    def facturacion_page() -> None:
        with AppShell():
            container = Container.get_instance()

            ui.label("Facturación").classes("text-2xl font-bold")

            # ── Filters ────────────────────────────────────────────────────────
            period_selector = ui.select(
                label="Período",
                options={},
                with_input=True,
                clearable=True,
            ).classes("w-64")

            filter_date_from = ui.input(
                label="Fecha desde",
                placeholder="YYYY-MM-DD",
            ).props("dense outlined").classes("w-40")
            filter_date_to = ui.input(
                label="Fecha hasta",
                placeholder="YYYY-MM-DD",
            ).props("dense outlined").classes("w-40")
            filter_desc = ui.input(
                label="Descripción",
                placeholder="Buscar por descripción...",
            ).props("dense outlined").classes("w-48")

            for f in [period_selector, filter_date_from, filter_date_to, filter_desc]:
                f.on("update:model-value", _render_invoices.refresh)

            total_label = ui.label("Total facturado: $0.00").classes(
                "text-lg font-semibold mt-2"
            )

            with ui.row().classes("items-center gap-2"):
                ui.button(
                    "Nueva Factura",
                    icon="add",
                    on_click=lambda: _invoice_dialog(None, _render_invoices.refresh),
                ).props("flat color=white")

            # ── Sorting state ─────────────────────────────────────────────────
            _sort_col = 0
            _sort_dir = -1  # default: newest first

            def _sort(col_idx: int) -> None:
                nonlocal _sort_col, _sort_dir
                if _sort_col == col_idx:
                    _sort_dir *= -1
                else:
                    _sort_col = col_idx
                    _sort_dir = 1
                _render_invoices.refresh()

            # ── Invoice list ─────────────────────────────────────────────────

            @ui.refreshable
            def _render_invoices() -> None:
                nonlocal _sort_col, _sort_dir

                invoices = container.obtener_facturas.execute()

                # Apply filters
                period_id = period_selector.value
                date_from = (filter_date_from.value or "").strip()
                date_to = (filter_date_to.value or "").strip()
                desc_q = (filter_desc.value or "").strip().lower()

                if period_id:
                    invoices = [
                        inv for inv in invoices
                        if str(inv.period_id) == period_id
                    ]
                if date_from:
                    try:
                        df = datetime.strptime(date_from, "%Y-%m-%d")
                        invoices = [inv for inv in invoices if inv.emited_date >= df]
                    except ValueError:
                        pass
                if date_to:
                    try:
                        dt = datetime.strptime(date_to, "%Y-%m-%d")
                        invoices = [inv for inv in invoices if inv.emited_date <= dt]
                    except ValueError:
                        pass
                if desc_q:
                    invoices = [
                        inv for inv in invoices
                        if inv.description and desc_q in inv.description.lower()
                    ]

                # Update total
                active_invoices = [inv for inv in invoices if inv.active]
                total_label.text = (
                    f"Total facturado: ${sum(inv.amount for inv in active_invoices):,.2f}"
                )

                if not invoices:
                    ui.label("No hay facturas registradas.").classes(
                        "text-gray-400 italic mt-4"
                    )
                    return

                # Sort
                _sort_keys = [
                    lambda inv: inv.invoice_number,
                    lambda inv: inv.emited_date,
                    lambda inv: inv.amount,
                    lambda inv: inv.description or "",
                    lambda inv: inv.active,
                ]
                invoices = sorted(
                    invoices, key=_sort_keys[_sort_col],
                    reverse=_sort_dir == -1,
                )

                # Define table columns
                table_columns = [
                    {'name': 'numero', 'label': 'Número', 'field': 'numero', 'align': 'left', 'sortable': True},
                    {'name': 'fecha', 'label': 'Fecha', 'field': 'fecha', 'align': 'left', 'sortable': True},
                    {'name': 'monto', 'label': 'Monto', 'field': 'monto', 'align': 'right', 'sortable': True},
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
                        'monto': f'${inv.amount:,.2f}',
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
                def _handle_edit(row: dict) -> None:
                    inv_id = row.get('invoice_id')
                    if inv_id:
                        inv = container.billing_repo.get_by_id(inv_id)
                        if inv:
                            with ui.dialog() as edit_dialog:
                                _invoice_dialog(inv, _render_invoices.refresh, edit_dialog)
                            edit_dialog.open()
                
                def _handle_toggle(row: dict) -> None:
                    inv_id = row.get('invoice_id')
                    if inv_id:
                        inv = container.billing_repo.get_by_id(inv_id)
                        if inv:
                            ui.notify(f"Toggle {inv_id} - TBD", type="info")
                
                table.on('edit', lambda e: _handle_edit(e.args))
                table.on('toggle', lambda e: _handle_toggle(e.args))

             # ── Toggle active ─────────────────────────────────────────────────

            @with_audit_user
            def _toggle_active(invoice_id: UUID, active: bool) -> None:
                try:
                    if active:
                        container.billing_repo.activate(invoice_id)
                    else:
                        container.billing_repo.inactivate(invoice_id)
                    ui.notify(
                        "Factura activada" if active else "Factura inactivada",
                        type="positive",
                    )
                    _render_invoices.refresh()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")

            # ── Period refresh ─────────────────────────────────────────────────
            def _refresh_periods() -> None:
                periods = container.period_repo.get_n_last(12)
                options = {str(p.period_id): p.period_name for p in periods}
                period_selector.options = options
                period_selector.update()
                _render_invoices.refresh()

            period_selector.on("update:model-value", _render_invoices.refresh)
            _refresh_periods()


# ── Invoice Dialog (create / edit) ──────────────────────────────────────────────


def _invoice_dialog(
    invoice: Invoice | None,
    refresh_fn: callable,
    existing_dialog: ui.dialog | None = None,
) -> None:
    """Open a dialog to create or edit an invoice.

    Args:
        invoice: Existing invoice to edit, or None to create new.
        refresh_fn: Called after successful save.
        existing_dialog: Reuse existing dialog instance (edit mode).
    """
    container = Container.get_instance()
    periods = container.period_repo.get_n_last(24)
    period_options = {str(p.period_id): p.period_name for p in periods}

    is_edit = invoice is not None

    if existing_dialog:
        dlg = existing_dialog
        # Content is already rendered inside the dialog
        _render_form(dlg, invoice, refresh_fn, period_options, container)
    else:
        with ui.dialog() as dlg, ui.card().classes("w-[400px] max-w-full"):
            _render_form(dlg, invoice, refresh_fn, period_options, container)
        dlg.open()


def _render_form(
    dlg: ui.dialog,
    invoice: Invoice | None,
    refresh_fn: callable,
    period_options: dict[str, str],
    container: Container,
) -> None:
    """Render the invoice form inside a dialog."""
    is_edit = invoice is not None
    ui.label("Editar Factura" if is_edit else "Nueva Factura").classes(
        "text-lg font-bold mb-2"
    )

    num_input = ui.input(
        label="Número de factura",
        value=invoice.invoice_number if invoice else "",
    ).classes("w-full")

    period_select = ui.select(
        label="Período",
        options=period_options,
        value=str(invoice.period_id) if invoice else None,
        with_input=True,
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
            pid = period_select.value
            date_str = (date_input.value or "").strip()
            amount = amount_input.value
            desc = (desc_input.value or "").strip() or None

            missing = []
            if not num:
                missing.append("Número")
            if not pid:
                missing.append("Período")
            if not date_str:
                missing.append("Fecha")
            if not amount or float(amount) <= 0:
                missing.append("Monto")

            if missing:
                ui.notify(
                    "Campos requeridos: " + ", ".join(missing),
                    type="warning",
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
                    kwargs["period_id"] = UUID(pid)
                    kwargs["emited_date"] = parsed_date
                    kwargs["amount"] = float(amount)
                    kwargs["description"] = desc

                    updated = Invoice(**kwargs)
                    container.billing_repo.update(invoice.invoice_id, updated)
                    ui.notify("Factura actualizada", type="positive")
                else:
                    inp = container.registrar_factura.Input(
                        invoice_number=num,
                        period_id=UUID(pid),
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
