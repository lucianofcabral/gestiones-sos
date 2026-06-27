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
            _sort_col = {"idx": 0, "dir": -1}

            def _sort_inv(col_idx: int) -> None:
                if _sort_col["idx"] == col_idx:
                    _sort_col["dir"] *= -1
                else:
                    _sort_col["idx"] = col_idx
                    _sort_col["dir"] = 1
                refresh_fn()

            _col_labels = [
                ("Número", "text-xs w-28"),
                ("Fecha", "text-xs w-24"),
                ("Importe", "text-xs w-24 text-right"),
                ("Descripción", "text-xs w-48"),
                ("Activo", "text-xs w-16"),
                ("", "text-xs w-20"),
            ]
            with ui.row().classes(
                "items-center gap-2 py-1 border-b border-gray-600 font-bold"
            ):
                for i, (label, cls) in enumerate(_col_labels):
                    arrow = (
                        " ▲" if _sort_col["idx"] == i and _sort_col["dir"] == 1
                        else " ▼" if _sort_col["idx"] == i
                        else ""
                    )
                    ui.label(f"{label}{arrow}").classes(
                        f"{cls} cursor-pointer"
                    ).on("click", lambda i=i: _sort_inv(i))

            # Sort
            _keys = [
                lambda i: i.invoice_number,
                lambda i: i.emited_date,
                lambda i: i.amount,
                lambda i: i.description or "",
                lambda i: i.active,
            ]
            sorted_inv = sorted(
                invoices, key=_keys[_sort_col["idx"]],
                reverse=_sort_col["dir"] == -1,
            )

            for inv in sorted_inv:
                with ui.row().classes("items-center gap-2 py-1 hover:bg-gray-800"):
                    ui.label(inv.invoice_number).classes("text-sm w-28")
                    ui.label(inv.emited_date.strftime("%Y-%m-%d")).classes(
                        "text-sm w-24 text-gray-400"
                    )
                    ui.label(f"${inv.amount:,.2f}").classes(
                        "text-sm w-24 text-right"
                    )
                    ui.label(inv.description or "—").classes(
                        "text-sm w-48 text-gray-400 truncate"
                    )
                    bc = "bg-green-600" if inv.active else "bg-red-600"
                    ui.label("Sí" if inv.active else "No").classes(
                        f"text-xs font-bold px-2 py-0.5 rounded-full "
                        f"{bc} text-white w-16 text-center"
                    )
                    with ui.row().classes("gap-1"):
                        # Edit
                        with ui.dialog() as edit_dlg:
                            _invoice_dialog(
                                inv, period, refresh_fn, container, edit_dlg,
                            )
                        ui.button(
                            icon="edit",
                            on_click=edit_dlg.open,
                        ).props("flat dense round size=sm")
                        # Toggle active
                        ui.button(
                            icon="toggle_off" if inv.active else "toggle_on",
                            on_click=lambda iid=inv.invoice_id,
                            active=inv.active: _toggle_invoice(
                                iid, not active, refresh_fn, container,
                            ),
                        ).props("flat dense round size=sm")
        else:
            ui.label("No hay facturas en este período.").classes(
                "text-sm text-gray-400 italic"
            )

        ui.separator().classes("my-4")

        # ── NC section ────────────────────────────────────────────────────
        ui.label("Notas de Crédito").classes("text-md font-bold mb-2")

        if ncs:
            with ui.row().classes(
                "items-center gap-2 py-1 border-b border-gray-600 font-bold"
            ):
                ui.label("ID Pago").classes("text-xs w-32")
                ui.label("Entregado").classes("text-xs w-20")
                ui.label("Fecha").classes("text-xs w-24")
                ui.label("").classes("text-xs w-20")

            for nc in ncs:
                with ui.row().classes("items-center gap-2 py-1 hover:bg-gray-800"):
                    ui.label(str(nc.payment_id)[:8] + "...").classes(
                        "text-sm w-32 text-gray-400"
                    )
                    badge_c = "bg-green-600" if nc.delivered else "bg-yellow-600"
                    ui.label("Sí" if nc.delivered else "No").classes(
                        f"text-xs font-bold px-2 py-0.5 rounded-full "
                        f"{badge_c} text-white w-20 text-center"
                    )
                    ui.label(nc.created_date.strftime("%Y-%m-%d")).classes(
                        "text-sm w-24 text-gray-400"
                    )
                    # Disassociate from period
                    ui.button(
                        icon="link_off",
                        on_click=lambda ncid=nc.nc_payment_id: _disassociate_nc(
                            ncid, refresh_fn, container,
                        ),
                    ).props(
                        "flat dense round size=sm"
                    ).tooltip("Desvincular del período")
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
