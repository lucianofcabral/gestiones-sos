"""Claim detail page — editable header card, type-specific Section 2, payments and documents."""

from uuid import UUID

from nicegui import ui

from src.application.use_cases.claims.actualizar_gestion import (
    ActualizarGestionInput,
)
from src.application.use_cases.claims.obtener_gestion_por_id import (
    ObtenerGestionPorIdInput,
)
from src.application.use_cases.payments.registrar_pago import (
    RegistrarPagoInput,
)
from src.domain.exceptions import ClaimNotFoundError
from src.infrastructure.container import Container, get_container
from src.ui.components.document_upload import DocumentUpload
from src.ui.components.shell import AppShell
from src.ui.services.audit_helper import with_audit_user


def register_gestiones_detalle_page() -> None:
    @ui.page("/gestiones/{id}")
    def gestiones_detalle_page(id: str) -> None:
        with AppShell():
            container = Container.get_instance()

            # ── Parse UUID ────────────────────────────────────────────────────
            try:
                claim_id = UUID(id)
            except ValueError:
                ui.notify("ID de gestión inválido", type="negative")
                ui.navigate.to("/gestiones")
                return

            # ── Back button (outside refreshable — always visible) ───────────
            ui.button(
                "← Volver a Gestiones",
                on_click=lambda: ui.navigate.to("/gestiones"),
            ).props("flat color=white")

            # ── Group options are stable, load once ──────────────────────────
            group_options = {
                str(g.group_id): g.name
                for g in container.obtener_grupos.execute()
            }

            # ── Refreshable claim card ─────────────────────────────────────
            @ui.refreshable
            def _render_claim_data() -> None:
                # Fetch fresh data every render
                try:
                    detalle = container.obtener_gestion_por_id.execute(
                        ObtenerGestionPorIdInput(claim_id=claim_id)
                    )
                except ClaimNotFoundError:
                    ui.notify("Gestión no encontrada", type="negative")
                    ui.navigate.to("/gestiones")
                    return
                except Exception as e:
                    ui.notify(f"Error al cargar detalle: {e}", type="negative")
                    return

                # Compute display values based on type
                is_grouped = detalle.grouped_data is not None
                type_badge = detalle.claim_kind_name
                reference = (
                    detalle.grouped_data.external_reference
                    if is_grouped and detalle.grouped_data
                    else (detalle.sos_records[0].gestion if detalle.sos_records
                          else str(detalle.claim_id)[:8])
                )
                reference_label = "Ref. Lote" if is_grouped else "Gestión N°"

                # ── Editable claim header card ────────────────────────────
                with ui.card().classes("w-full mt-2 p-3"):
                    with ui.row().classes("items-center gap-2 mb-2"):
                        ui.label("Detalle de Gestión").classes("text-xl font-bold")
                        ui.label(type_badge).classes(
                            "text-xs font-bold px-2 py-1 rounded-full "
                            "bg-blue-600 text-white"
                        )

                    # ── 2-column grid ───────────────────────────────────
                    with ui.grid(columns=2).classes("gap-x-4 gap-y-1"):
                        with ui.column().classes("gap-0"):
                            ui.label("Asegurado").classes("text-xs text-gray-400")
                            name_input = ui.input(value=detalle.claimer_name).classes("w-full")

                        with ui.column().classes("gap-0"):
                            ui.label(reference_label).classes("text-xs text-gray-400")
                            ui.label(str(reference)).classes("text-sm text-gray-300")

                        with ui.column().classes("gap-0"):
                            ui.label("Póliza").classes("text-xs text-gray-400")
                            policy_input = ui.input(value=detalle.policy_number).classes("w-full")

                        with ui.column().classes("gap-0"):
                            ui.label("Patente").classes("text-xs text-gray-400")
                            plate_input = ui.input(value=detalle.plate).classes("w-full")

                        with ui.column().classes("gap-0"):
                            ui.label("Monto").classes("text-xs text-gray-400")
                            amount_input = ui.number(
                                value=detalle.claimed_amount, precision=2,
                            ).classes("w-full")

                        with ui.column().classes("gap-0"):
                            ui.label("Grupo").classes("text-xs text-gray-400")
                            cur_group = str(detalle.group_id) if detalle.group_id else None
                            group_sel = ui.select(
                                options=group_options,
                                value=cur_group,
                                with_input=True,
                                clearable=True,
                            ).classes("w-full")

                        with ui.column().classes("gap-0"):
                            ui.label("Tipo").classes("text-xs text-gray-400")
                            ui.label(detalle.claim_kind_name).classes("text-sm text-gray-300")

                        with ui.column().classes("gap-0"):
                            ui.label("Fecha").classes("text-xs text-gray-400")
                            ui.label(detalle.created_at.strftime("%Y-%m-%d %H:%M")).classes(
                                "text-sm text-gray-300"
                            )

                        with ui.row().classes("gap-6"):
                            with ui.column().classes("gap-0"):
                                ui.label("Resuelto").classes("text-xs text-gray-400")
                                solved_check = ui.checkbox(value=detalle.solved)
                            with ui.column().classes("gap-0"):
                                ui.label("Activo").classes("text-xs text-gray-400")
                                active_check = ui.checkbox(value=detalle.active)

                    # ── Comment — full width ─────────────────────────────
                    ui.label("Comentario").classes("text-xs text-gray-400 mt-1")
                    comment_input = ui.textarea(
                        value=detalle.comment or "",
                    ).classes("w-full").props("rows=1")

                    with ui.row().classes("justify-end mt-2 gap-2"):
                        ui.button(
                            "Descartar",
                            on_click=lambda: _render_claim_data.refresh(),
                        ).props("flat")

                        @with_audit_user
                        def _guardar_cambios() -> None:
                            try:
                                container.actualizar_gestion.execute(
                                    ActualizarGestionInput(
                                        claim_id=claim_id,
                                        group_id=UUID(group_sel.value) if group_sel.value else None,
                                        claimer_name=name_input.value.strip(),
                                        policy_number=policy_input.value.strip(),
                                        plate=plate_input.value.strip(),
                                        claimed_amount=amount_input.value or 0.0,
                                        comment=comment_input.value.strip(),
                                        solved=solved_check.value,
                                        active=active_check.value,
                                    )
                                )
                                ui.notify("Gestión actualizada", type="positive")
                                _render_claim_data.refresh()
                            except ValueError as e:
                                ui.notify(str(e), type="negative")
                            except Exception as e:
                                ui.notify(f"Error al guardar: {e}", type="negative")

                        ui.button(
                            "Guardar Cambios",
                            icon="save",
                            on_click=_guardar_cambios,
                        ).props("color=primary")

            # ── Two-column: banner (left) | documents + payments (right) ──
            with ui.row().classes("w-full gap-4 items-start"):

                # ── Left: claim card ──────────────────────────────────────
                with ui.column().classes("flex-[3] min-w-0"):
                    _render_claim_data()

                # ── Right: documents (top) + payments (bottom) ───────────
                with ui.column().classes("flex-[2] min-w-0 gap-0"):
                    _render_documents_section(claim_id)
                    _render_payments_section(container, claim_id)


# ── Render helpers ─────────────────────────────────────────────────────────────


def _render_payments_section(container: Container, claim_id: UUID) -> None:
    """Section 3 — Payments table with create, edit, and inactivate."""

    # Pre-load option lists once (stable data)
    agent_options = {str(a.agent_id): a.name for a in container.agent_repo.get_all()}
    via_options = {str(v.payment_via_id): v.name for v in container.payment_via_repo.get_all()}
    nc_via = container.payment_via_repo.get_nc()
    nc_via_id = str(nc_via.payment_via_id) if nc_via else None
    sos_id = str(container.agent_repo.get_sos().agent_id) if container.agent_repo.get_sos() else None
    sm_id = str(container.agent_repo.get_sm().agent_id) if container.agent_repo.get_sm() else None

    def _handle_inactivate(payment_id: UUID) -> None:
        try:
            result = container.inactivar_pago.execute(
                type("Inp", (), {"payment_id": payment_id})()
            )
            if result.success:
                ui.notify("Pago desactivado", type="positive")
            else:
                ui.notify(result.reason or "No se pudo desactivar", type="warning")
            _refresh_pagos.refresh()
        except Exception as e:
            ui.notify(f"Error: {e}", type="negative")

    def _open_dialog(payment_id: UUID | None = None) -> None:
        if payment_id:
            pmt = container.obtener_pagos.get_by_id(payment_id)
        else:
            pmt = None
        _pago_dialog(container, claim_id, pmt, _refresh_pagos,
                     agent_options, via_options, nc_via_id, sos_id, sm_id)

    @ui.refreshable
    def _refresh_pagos() -> None:
        payments = container.obtener_pagos.get_by_claim_id(claim_id)

        with ui.row().classes("items-center justify-between mt-4 mb-1"):
            ui.label("Pagos").classes("text-lg font-bold")
            ui.button(
                "Nuevo Pago",
                icon="add",
                on_click=lambda: _open_dialog(),
            ).props("flat color=white size=sm")

        if not payments:
            ui.label("No hay pagos registrados para esta gestión.").classes(
                "text-gray-400 italic"
            )
            return

        with ui.row().classes("items-center gap-2 py-1 border-b border-gray-600 font-bold"):
            for label, width in [
                ("Monto", "w-28"),
                ("Fecha", "w-28"),
                ("Pagador", "w-24"),
                ("Benef.", "w-24"),
                ("Activo", "w-16"),
                ("", "w-20"),
            ]:
                ui.label(label).classes(f"text-xs {width}")

        for pmt in sorted(payments, key=lambda p: p.created_date, reverse=True):
            payer_name = agent_options.get(str(pmt.payer_id), "—")
            payee_name = agent_options.get(str(pmt.payee_id), "—")
            with ui.row().classes("items-center gap-2 py-1 hover:bg-gray-800"):
                ui.label(f"${pmt.amount:,.2f}").classes("text-sm w-28 text-right")
                ui.label(pmt.created_date.strftime("%Y-%m-%d")).classes(
                    "text-sm w-28 text-gray-400"
                )
                ui.label(payer_name).classes("text-sm w-24 truncate")
                ui.label(payee_name).classes("text-sm w-24 truncate")
                ui.label("Sí" if pmt.active else "No").classes("text-sm w-16")
                with ui.row().classes("gap-1 w-20"):
                    ui.button(
                        icon="edit",
                        on_click=lambda pid=pmt.payment_id: _open_dialog(pid),
                    ).props("flat dense round size=sm")
                    ui.button(
                        icon="toggle_off" if pmt.active else "toggle_on",
                        on_click=lambda pid=pmt.payment_id: _handle_inactivate(pid),
                    ).props(f"flat dense round size=sm color={'grey' if not pmt.active else 'orange-7'}")

    _refresh_pagos()


def _pago_dialog(
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
    """Create or edit a payment dialog."""
    is_edit = payment is not None

    with ui.dialog() as dlg, ui.card().classes("min-w-[400px]"):
        ui.label("Editar Pago" if is_edit else "Nuevo Pago").classes("text-lg font-bold mb-2")

        payer_sel = ui.select(
            label="Pagador", options=agent_options,
            value=str(payment.payer_id) if payment else None,
            with_input=True,
        ).classes("w-full")
        payee_sel = ui.select(
            label="Beneficiario", options=agent_options,
            value=str(payment.payee_id) if payment else None,
            with_input=True,
        ).classes("w-full")
        via_sel = ui.select(
            label="Medio de Pago", options=via_options,
            value=str(payment.payment_via_id) if payment else None,
            with_input=True,
        ).classes("w-full")
        amount_input = ui.number(
            label="Monto", precision=2,
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

        # Apply on initial load + on change
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
                    ui.notify("Campos requeridos: " + ", ".join(missing), type="warning")
                    return

                try:
                    if is_edit:
                        container.actualizar_pago.execute(
                            type("Inp", (), {
                                "payment_id": payment.payment_id,
                                "payer_id": UUID(payer_val),
                                "payee_id": UUID(payee_val),
                                "payment_via_id": UUID(via_val),
                                "amount": float(amount_val),
                            })()
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


# ── Document section ────────────────────────────────────────────────────────────


def _render_documents_section(claim_id: UUID) -> None:
    """Section 4 — Document upload & gallery for a claim."""
    container = get_container()

    with ui.row().classes("items-center justify-between mt-4 mb-1"):
        ui.label("Documentos").classes("text-lg font-bold")

    DocumentUpload(
        entity_type="claim",
        entity_id=claim_id,
        on_upload=lambda: _refresh_docs.refresh(),
    ).render()

    def _desasociar_doc(doc_id: UUID) -> None:
        try:
            container.desasociar_documento.execute(
                doc_id, "claim", claim_id
            )
            ui.notify("Documento desasociado", type="positive")
            _refresh_docs.refresh()
        except Exception as e:
            ui.notify(f"Error al desasociar: {e}", type="negative")

    @ui.refreshable
    def _refresh_docs() -> None:
        docs = container.obtener_documentos.by_entity("claim", claim_id)
        if not docs:
            ui.label("No hay documentos vinculados.").classes(
                "text-gray-400 italic mt-2"
            )
            return

        with ui.row().classes(
            "items-center gap-2 py-1 border-b border-gray-600 font-bold mt-1"
        ):
            ui.label("Nombre").classes("text-xs w-44")
            ui.label("Tipo").classes("text-xs w-20")
            ui.label("Tamaño").classes("text-xs w-20 text-right")
            ui.label("Fecha").classes("text-xs w-28")
            ui.label("").classes("w-24")

        for doc in sorted(docs, key=lambda d: d.created_at, reverse=True):
            with ui.row().classes(
                "items-center gap-2 py-1 hover:bg-gray-800"
            ):
                ui.label(doc.name).classes("text-sm w-44 truncate")
                ui.label(doc.type).classes("text-sm w-20")
                ui.label(_format_size(doc.size)).classes(
                    "text-sm w-20 text-right text-gray-400"
                )
                ui.label(doc.created_at.strftime("%Y-%m-%d")).classes(
                    "text-sm w-28 text-gray-400"
                )
                with ui.row().classes("gap-1 w-24"):
                    ui.button(
                        icon="download",
                        on_click=lambda did=doc.document_id: ui.navigate.to(
                            f"/api/documents/{did}/file"
                        ),
                    ).props("flat dense round size=sm")
                    ui.button(
                        icon="link_off",
                        on_click=lambda did=doc.document_id: _desasociar_doc(did),
                    ).props("flat dense round size=sm color=orange-7")

    _refresh_docs()


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
