"""Facturación page — period selector, invoice list, create form, delete button."""

from datetime import datetime
from uuid import UUID

from nicegui import ui

from src.infrastructure.container import Container
from src.ui.components.shell import AppShell


def register_facturacion_page() -> None:
    @ui.page("/facturas")
    def facturacion_page() -> None:
        with AppShell():
            container = Container.get_instance()

            ui.label("Facturación").classes("text-2xl font-bold")

            # ── Period selector + total label ────────────────────────────────
            period_selector = ui.select(
                label="Período",
                options={},  # filled on refresh
                with_input=True,
            ).classes("w-64")

            total_label = ui.label("Total facturado: $0.00").classes(
                "text-lg font-semibold mt-2"
            )

            # ── Create form ──────────────────────────────────────────────────
            with ui.card().classes("w-full max-w-md mt-4 p-4"):
                ui.label("Nueva Factura").classes("text-lg font-bold")

                inv_number_input = ui.input(
                    label="Número de factura",
                    placeholder="Ej: F001-2024",
                )
                period_select_form = ui.select(
                    label="Período",
                    options={},
                    with_input=True,
                )
                date_input = ui.input(
                    label="Fecha de emisión",
                    placeholder="YYYY-MM-DD",
                )
                amount_input = ui.number(
                    label="Monto",
                    precision=2,
                )

                async def _create_invoice() -> None:
                    inv_number = inv_number_input.value.strip()
                    period_id = period_select_form.value
                    date_str = date_input.value.strip()
                    amount = amount_input.value

                    if not inv_number or not period_id or not date_str or not amount:
                        ui.notify("Todos los campos son obligatorios", type="warning")
                        return

                    try:
                        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        ui.notify("Fecha inválida. Use YYYY-MM-DD", type="warning")
                        return

                    try:
                        inp = container.registrar_factura.Input(
                            invoice_number=inv_number,
                            period_id=UUID(period_id),
                            emited_date=parsed_date,
                            amount=float(amount),
                        )
                        container.registrar_factura.execute(inp)
                        ui.notify("Factura registrada", type="positive")
                        inv_number_input.value = ""
                        date_input.value = ""
                        amount_input.value = None
                        _render_invoices.refresh()
                    except Exception as e:
                        ui.notify(f"Error: {e}", type="negative")

                ui.button(
                    "Registrar",
                    icon="add",
                    on_click=_create_invoice,
                )

            # ── Invoice list ─────────────────────────────────────────────────

            @ui.refreshable
            def _render_invoices() -> None:
                selected_period_id = period_selector.value

                if selected_period_id:
                    invoices = container.obtener_facturas.por_periodo(
                        UUID(selected_period_id)
                    )
                else:
                    invoices = container.obtener_facturas.execute()

                # Update total
                total = sum(inv.amount for inv in invoices)
                total_label.text = f"Total facturado: ${total:,.2f}"

                rows = [
                    {
                        "invoice_number": inv.invoice_number,
                        "emited_date": inv.emited_date.strftime("%Y-%m-%d"),
                        "amount": f"${inv.amount:,.2f}",
                        "actions": _delete_button(inv.invoice_id, _render_invoices),
                    }
                    for inv in invoices
                ]

                for row in rows:
                    with ui.row().classes("items-center gap-4 py-1"):
                        ui.label(row["invoice_number"]).classes("text-sm w-32")
                        ui.label(row["emited_date"]).classes(
                            "text-sm w-28 text-gray-400"
                        )
                        ui.label(row["amount"]).classes("text-sm w-24 text-right")
                        row["actions"]

            def _delete_button(invoice_id: UUID, refresh_fn) -> ui.button:
                def _do_delete() -> None:
                    try:
                        container.eliminar_factura.execute(invoice_id)
                        ui.notify("Factura eliminada", type="positive")
                        refresh_fn.refresh()
                    except ValueError as e:
                        ui.notify(str(e), type="negative")
                    except Exception as e:
                        ui.notify(f"Error: {e}", type="negative")

                return ui.button(
                    "Eliminar",
                    icon="delete",
                    on_click=_do_delete,
                ).props("flat size=sm")

            # ── Refresh periods on load ──────────────────────────────────────
            def _refresh_periods() -> None:
                periods = container.period_repo.get_n_last(12)
                options = {str(p.period_id): p.period_name for p in periods}
                period_selector.options = options
                period_selector.update()
                period_select_form.options = options
                period_select_form.update()
                _render_invoices.refresh()

            period_selector.on("update:model-value", _render_invoices.refresh)

            _refresh_periods()
