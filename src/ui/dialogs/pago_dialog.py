"""Shared payment and credit-note dialogs extracted from gestiones_detalle.py."""

from uuid import UUID

from nicegui import ui

from src.application.use_cases.payments.registrar_pago import (
    RegistrarPagoInput,
)
from src.infrastructure.container import Container
from src.ui.services.audit_helper import with_audit_user


def pago_dialog(
    container: Container,
    claim_id: UUID,
    payment: object | None,
    on_save: object,
    agent_options: dict,
    via_options: dict,
    nc_via_id: str | None,
    sos_id: str | None,
    sm_id: str | None,
) -> None:
    """Create or edit a payment dialog. Extracted from gestiones_detalle.py."""
    is_edit = payment is not None

    with ui.dialog() as dlg, ui.card().classes("min-w-[400px]"):
        ui.label("Editar Pago" if is_edit else "Nuevo Pago").classes(
            "text-lg font-bold mb-2"
        )

        payer_sel = ui.select(
            label="Pagador",
            options=agent_options,
            value=str(payment.payer_id) if payment else None,
            with_input=True,
        ).classes("w-full")
        payee_sel = ui.select(
            label="Beneficiario",
            options=agent_options,
            value=str(payment.payee_id) if payment else None,
            with_input=True,
        ).classes("w-full")
        via_sel = ui.select(
            label="Medio de Pago",
            options=via_options,
            value=str(payment.payment_via_id) if payment else None,
            with_input=True,
        ).classes("w-full")
        amount_input = ui.number(
            label="Monto",
            precision=2,
            value=payment.amount if payment else None,
        ).classes("w-full")

        def _apply_nc_defaults() -> None:
            """When NC is selected: auto-lock SOS/SM, no period needed."""
            is_nc = via_sel.value == nc_via_id
            if is_nc and sos_id:
                payer_sel.value = sos_id
                payer_sel.disable()
            else:
                payer_sel.enable()
            if is_nc and sm_id:
                payee_sel.value = sm_id
                payee_sel.disable()
            else:
                payee_sel.enable()

        _apply_nc_defaults()
        via_sel.on("update:model-value", _apply_nc_defaults)

        with ui.row().classes("gap-2 justify-end mt-3"):
            ui.button("Cancelar", on_click=dlg.close).props("flat")

            @with_audit_user
            async def _save() -> None:
                missing = []
                payer_val = payer_sel.value
                payee_val = payee_sel.value
                via_val = via_sel.value
                amount_val = amount_input.value

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
                        "Campos requeridos: " + ", ".join(missing), type="warning"
                    )
                    return

                try:
                    if is_edit:
                        container.actualizar_pago.execute(
                            type(
                                "Inp",
                                (),
                                {
                                    "payment_id": payment.payment_id,
                                    "payer_id": UUID(payer_val),
                                    "payee_id": UUID(payee_val),
                                    "payment_via_id": UUID(via_val),
                                    "amount": float(amount_val),
                                },
                            )()
                        )
                        ui.notify("Pago actualizado", type="positive")
                    else:
                        container.registrar_pago.execute(
                            RegistrarPagoInput(
                                claim_id=claim_id,
                                payer_id=UUID(payer_val),
                                payee_id=UUID(payee_val),
                                payment_via_id=UUID(via_val),
                                amount=float(amount_val),
                                period_id=None,
                            )
                        )
                        ui.notify("Pago registrado", type="positive")
                    dlg.close()
                    on_save.refresh()
                except ValueError as e:
                    ui.notify(str(e), type="negative")
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")

            ui.button("Guardar", on_click=_save).props("color=primary")

    dlg.open()


def editar_nc_dialog(
    container: Container,
    payment_id: UUID,
    on_save: object,
) -> None:
    """Edit an existing NC payment — only amount editable, inactivate supported."""
    payment = container.payment_repo.get_by_id(payment_id)
    if payment is None:
        ui.notify("No se encontró el pago de la NC", type="negative")
        return

    with ui.dialog() as dlg, ui.card().classes("min-w-[400px]"):
        ui.label("Editar Nota de Crédito").classes("text-lg font-bold mb-2")

        payer_sel = ui.select(
            label="Pagador",
            options={
                str(a.agent_id): a.name
                for a in container.agent_repo.get_all()
            },
            value=str(payment.payer_id),
        ).classes("w-full")
        payer_sel.disable()

        payee_sel = ui.select(
            label="Beneficiario",
            options={
                str(a.agent_id): a.name
                for a in container.agent_repo.get_all()
            },
            value=str(payment.payee_id),
        ).classes("w-full")
        payee_sel.disable()

        via_sel = ui.select(
            label="Medio de Pago",
            options={
                str(v.payment_via_id): v.name
                for v in container.payment_via_repo.get_all()
            },
            value=str(payment.payment_via_id),
        ).classes("w-full")
        via_sel.disable()

        amount_input = ui.number(
            label="Monto",
            precision=2,
            value=payment.amount,
        ).classes("w-full")

        with ui.row().classes("gap-2 justify-end mt-3"):
            ui.button("Cancelar", on_click=dlg.close).props("flat")

            @with_audit_user
            async def _inactivate() -> None:
                try:
                    container.inactivar_pago.execute(
                        type("Inp", (), {"payment_id": payment.payment_id})()
                    )
                    ui.notify("Nota de Crédito inactivada", type="positive")
                    dlg.close()
                    on_save.refresh()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")

            ui.button(
                "Inactivar",
                on_click=_inactivate,
                icon="toggle_off",
            ).props("color=negative flat")

            @with_audit_user
            async def _save() -> None:
                amount_val = amount_input.value
                if not amount_val or float(amount_val) <= 0:
                    ui.notify("El monto debe ser mayor a cero", type="warning")
                    return

                try:
                    container.actualizar_pago.execute(
                        type(
                            "Inp",
                            (),
                            {
                                "payment_id": payment.payment_id,
                                "amount": float(amount_val),
                            },
                        )()
                    )
                    ui.notify("Nota de Crédito actualizada", type="positive")
                    dlg.close()
                    on_save.refresh()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")

            ui.button("Guardar", on_click=_save).props("color=primary")

    dlg.open()


def credito_dialog(
    container: Container,
    claim_id: UUID,
    on_save: object,
    agent_options: dict,
    via_options: dict,
    nc_via_id: str,
    sos_id: str,
    sm_id: str,
) -> None:
    """NC-only payment dialog: locked payer=SOS, payee=SM, medio=NC."""
    with ui.dialog() as dlg, ui.card().classes("min-w-[400px]"):
        ui.label("Nota de Crédito").classes("text-lg font-bold mb-2")

        ui.label(
            "NC: Pagador SOS, Beneficiario SM, Medio NC (bloqueado)"
        ).classes("text-xs text-yellow-400 mb-2")

        payer_sel = ui.select(
            label="Pagador",
            options=agent_options,
            value=sos_id,
            with_input=True,
        ).classes("w-full")
        payer_sel.disable()

        payee_sel = ui.select(
            label="Beneficiario",
            options=agent_options,
            value=sm_id,
            with_input=True,
        ).classes("w-full")
        payee_sel.disable()

        via_sel = ui.select(
            label="Medio de Pago",
            options=via_options,
            value=nc_via_id,
            with_input=True,
        ).classes("w-full")
        via_sel.disable()

        amount_input = ui.number(
            label="Monto",
            precision=2,
        ).classes("w-full")

        with ui.row().classes("gap-2 justify-end mt-3"):
            ui.button("Cancelar", on_click=dlg.close).props("flat")

            @with_audit_user
            async def _save() -> None:
                amount_val = amount_input.value
                if not amount_val or float(amount_val) <= 0:
                    ui.notify("El monto debe ser mayor a cero", type="warning")
                    return

                try:
                    container.registrar_pago.execute(
                        RegistrarPagoInput(
                            claim_id=claim_id,
                            payer_id=UUID(sos_id),
                            payee_id=UUID(sm_id),
                            payment_via_id=UUID(nc_via_id),
                            amount=float(amount_val),
                            period_id=None,
                        )
                    )
                    ui.notify("Nota de Crédito registrada", type="positive")
                    dlg.close()
                    on_save.refresh()
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")

            ui.button("Guardar", on_click=_save).props("color=primary")

    dlg.open()
