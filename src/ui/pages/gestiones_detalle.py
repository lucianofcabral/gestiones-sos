"""Claim detail page — editable header card, type-specific Section 2, payments and documents."""

from uuid import UUID

from nicegui import app, ui

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
            back_url = app.storage.user.pop("return_to", "/gestiones")
            ui.button(
                f"← Volver{' a Documentos' if back_url != '/gestiones' else ' a Gestiones'}",
                on_click=lambda: ui.navigate.to(back_url),
            ).props("flat color=white")

            # ── Group options are stable, load once ──────────────────────────
            group_options = {
                str(g.group_id): g.name for g in container.obtener_grupos.execute()
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
                    else (
                        detalle.sos_records[0].gestion
                        if detalle.sos_records
                        else str(detalle.claim_id)[:8]
                    )
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
                            name_input = ui.input(value=detalle.claimer_name).classes(
                                "w-full"
                            )

                        with ui.column().classes("gap-0"):
                            ui.label(reference_label).classes("text-xs text-gray-400")
                            ui.label(str(reference)).classes("text-sm text-gray-300")

                        with ui.column().classes("gap-0"):
                            ui.label("Póliza").classes("text-xs text-gray-400")
                            policy_input = ui.input(
                                value=detalle.policy_number
                            ).classes("w-full")

                        with ui.column().classes("gap-0"):
                            ui.label("Patente").classes("text-xs text-gray-400")
                            plate_input = ui.input(value=detalle.plate).classes(
                                "w-full"
                            )

                        with ui.column().classes("gap-0"):
                            ui.label("Monto").classes("text-xs text-gray-400")
                            amount_input = ui.number(
                                value=detalle.claimed_amount,
                                precision=2,
                            ).classes("w-full")

                        with ui.column().classes("gap-0"):
                            ui.label("Grupo").classes("text-xs text-gray-400")
                            cur_group = (
                                str(detalle.group_id) if detalle.group_id else None
                            )
                            group_sel = ui.select(
                                options=group_options,
                                value=cur_group,
                                with_input=True,
                                clearable=True,
                            ).classes("w-full")

                        with ui.column().classes("gap-0"):
                            ui.label("Tipo").classes("text-xs text-gray-400")
                            ui.label(detalle.claim_kind_name).classes(
                                "text-sm text-gray-300"
                            )

                        with ui.column().classes("gap-0"):
                            ui.label("Fecha").classes("text-xs text-gray-400")
                            ui.label(
                                detalle.created_at.strftime("%Y-%m-%d %H:%M")
                            ).classes("text-sm text-gray-300")

                        with ui.row().classes("gap-6"):
                            with ui.column().classes("gap-0"):
                                ui.label("Resuelto").classes("text-xs text-gray-400")
                                solved_check = ui.checkbox(value=detalle.solved)
                            with ui.column().classes("gap-0"):
                                ui.label("Activo").classes("text-xs text-gray-400")
                                active_check = ui.checkbox(value=detalle.active)

                    # ── Comment — full width ─────────────────────────────
                    ui.label("Comentario").classes("text-xs text-gray-400 mt-1")
                    comment_input = (
                        ui.textarea(
                            value=detalle.comment or "",
                        )
                        .classes("w-full")
                        .props("rows=1")
                    )

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
                                        group_id=UUID(group_sel.value)
                                        if group_sel.value
                                        else None,
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
    via_options = {
        str(v.payment_via_id): v.name for v in container.payment_via_repo.get_all()
    }
    nc_via = container.payment_via_repo.get_nc()
    nc_via_id = str(nc_via.payment_via_id) if nc_via else None
    sos_id = (
        str(container.agent_repo.get_sos().agent_id)
        if container.agent_repo.get_sos()
        else None
    )
    sm_id = (
        str(container.agent_repo.get_sm().agent_id)
        if container.agent_repo.get_sm()
        else None
    )

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
        _pago_dialog(
            container,
            claim_id,
            pmt,
            _refresh_pagos,
            agent_options,
            via_options,
            nc_via_id,
            sos_id,
            sm_id,
        )

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

        # Define columns for payments table
        payment_columns = [
            {'name': 'monto', 'label': 'Monto', 'field': 'monto', 'align': 'right', 'sortable': True, 'style': 'min-width: 120px;'},
            {'name': 'fecha', 'label': 'Fecha', 'field': 'fecha', 'align': 'left', 'sortable': True, 'style': 'min-width: 120px;'},
            {'name': 'pagador', 'label': 'Pagador', 'field': 'pagador', 'align': 'left', 'sortable': True, 'style': 'min-width: 120px;'},
            {'name': 'beneficiario', 'label': 'Benef.', 'field': 'beneficiario', 'align': 'left', 'sortable': True, 'style': 'min-width: 120px;'},
            {'name': 'activo', 'label': 'Activo', 'field': 'activo', 'align': 'center', 'sortable': True, 'style': 'min-width: 80px;'},
            {'name': 'acciones', 'label': 'Acciones', 'field': 'acciones', 'align': 'center', 'sortable': False, 'style': 'min-width: 100px;'},
        ]

        # Prepare table data
        payment_rows = []
        for pmt in sorted(payments, key=lambda p: p.created_date, reverse=True):
            payer_name = agent_options.get(str(pmt.payer_id), "—")
            payee_name = agent_options.get(str(pmt.payee_id), "—")
            payment_rows.append({
                'id': str(pmt.payment_id),
                'payment_id': pmt.payment_id,
                'monto': f"${pmt.amount:,.2f}",
                'fecha': pmt.created_date.strftime("%Y-%m-%d"),
                'pagador': payer_name,
                'beneficiario': payee_name,
                'activo': "Sí" if pmt.active else "No",
                'is_active': pmt.active,
            })

        # Create table
        table = ui.table(columns=payment_columns, rows=payment_rows, row_key='id').classes('w-full')

        # Add action icons slot
        table.add_slot('body-cell-acciones', '''
            <q-td :props="props" class="text-center gap-1">
                <q-btn icon="edit" @click="$parent.$emit('edit', props.row)" flat dense color="blue" size="sm" />
                <q-btn :icon="props.row.is_active ? 'toggle_off' : 'toggle_on'" @click="$parent.$emit('toggle', props.row)" flat dense :color="props.row.is_active ? 'orange-7' : 'grey'" size="sm" />
            </q-td>
        ''')

        # Register handlers
        def _handle_edit(row: dict) -> None:
            _open_dialog(row.get('payment_id'))

        def _handle_toggle(row: dict) -> None:
            _handle_inactivate(row.get('payment_id'))

        table.on('edit', lambda e: _handle_edit(e.args))
        table.on('toggle', lambda e: _handle_toggle(e.args))

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
            container.desasociar_documento.execute(doc_id, "claim", claim_id)
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

        # Define columns for documents table
        doc_columns = [
            {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre', 'align': 'left', 'sortable': True, 'style': 'flex: 1; min-width: 150px;'},
            {'name': 'tipo', 'label': 'Tipo', 'field': 'tipo', 'align': 'left', 'sortable': True, 'style': 'min-width: 100px;'},
            {'name': 'tamaño', 'label': 'Tamaño', 'field': 'tamaño', 'align': 'right', 'sortable': True, 'style': 'min-width: 100px;'},
            {'name': 'fecha', 'label': 'Fecha', 'field': 'fecha', 'align': 'left', 'sortable': True, 'style': 'min-width: 100px;'},
            {'name': 'acciones', 'label': 'Acciones', 'field': 'acciones', 'align': 'center', 'sortable': False, 'style': 'min-width: 100px;'},
        ]

        # Prepare table data
        doc_rows = []
        for doc in sorted(docs, key=lambda d: d.created_at, reverse=True):
            doc_rows.append({
                'id': str(doc.document_id),
                'document_id': doc.document_id,
                'nombre': doc.name,
                'tipo': doc.type,
                'tamaño': _format_size(doc.size),
                'fecha': doc.created_at.strftime("%Y-%m-%d"),
            })

        # Create table
        table = ui.table(columns=doc_columns, rows=doc_rows, row_key='id').classes('w-full mt-1')

        # Add action icons slot
        table.add_slot('body-cell-acciones', '''
            <q-td :props="props" class="text-center gap-1">
                <q-btn icon="download" @click="$parent.$emit('download', props.row)" flat dense color="blue" size="sm" />
                <q-btn icon="link_off" @click="$parent.$emit('unlink', props.row)" flat dense color="orange-7" size="sm" />
            </q-td>
        ''')

        # Register handlers
        def _handle_download(row: dict) -> None:
            ui.navigate.to(f"/api/documents/{row.get('document_id')}/file")

        def _handle_unlink(row: dict) -> None:
            _desasociar_doc(row.get('document_id'))

        table.on('download', lambda e: _handle_download(e.args))
        table.on('unlink', lambda e: _handle_unlink(e.args))

    _refresh_docs()


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
