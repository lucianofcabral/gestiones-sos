"""Claim detail page — header card, type-specific Section 2, and payments table."""

from uuid import UUID

from nicegui import ui

from src.application.use_cases.claims.actualizar_grupo_de_gestion import (
    ActualizarGrupoDeGestionInput,
)
from src.application.use_cases.claims.obtener_gestion_por_id import (
    ObtenerGestionPorIdInput,
)
from src.application.use_cases.payments.registrar_pago import (
    RegistrarPagoInput,
)
from src.domain.exceptions import ClaimNotFoundError
from src.infrastructure.container import Container
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

            # ── Fetch data ────────────────────────────────────────────────────
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

            # ── Back button ───────────────────────────────────────────────────
            ui.button(
                "← Volver a Gestiones",
                on_click=lambda: ui.navigate.to("/gestiones"),
            ).props("flat color=white")

            # ── Section 1: Claim header card ──────────────────────────────────
            with ui.card().classes("w-full mt-4 p-4"):
                with ui.row().classes("items-center gap-2 mb-2"):
                    ui.label("Detalle de Gestión").classes("text-xl font-bold")
                    ui.label(type_badge).classes(
                        "text-xs font-bold px-2 py-1 rounded-full "
                        "bg-blue-600 text-white"
                    )

                with ui.grid(columns=3).classes("gap-4"):
                    _field(reference_label, str(reference))
                    _field("Asegurado", detalle.claimer_name)
                    _field("Póliza", detalle.policy_number)
                    _field("Patente", detalle.plate)
                    _field("Monto", f"${detalle.claimed_amount:,.2f}")
                    with ui.column().classes("gap-0"):
                        ui.label("Grupo").classes("text-xs text-gray-400")
                        group_options = {
                            str(g.group_id): g.name
                            for g in container.obtener_grupos.execute()
                        }
                        cur_group = str(detalle.group_id) if detalle.group_id else None
                        group_sel = ui.select(
                            options=group_options,
                            value=cur_group,
                            with_input=True,
                        ).classes("text-sm")

                        @with_audit_user
                        async def _on_group_change() -> None:
                            new_val = group_sel.value
                            if not new_val or new_val == cur_group:
                                return
                            try:
                                container.actualizar_grupo_de_gestion.execute(
                                    ActualizarGrupoDeGestionInput(
                                        claim_id=detalle.claim_id,
                                        new_group_id=UUID(new_val),
                                    )
                                )
                                ui.notify("Grupo actualizado", type="positive")
                                ui.navigate.reload()
                            except ValueError as e:
                                ui.notify(str(e), type="negative")
                            except Exception as e:
                                ui.notify(f"Error al actualizar grupo: {e}", type="negative")

                        group_sel.on("update:model-value", _on_group_change)
                    _field("Tipo", detalle.claim_kind_name)
                    _field("Resuelto", "Sí" if detalle.solved else "No")
                    _field("Activo", "Sí" if detalle.active else "No")
                    _field(
                        "Fecha",
                        detalle.created_at.strftime("%Y-%m-%d %H:%M"),
                    )
                    if detalle.comment:
                        _field("Comentario", detalle.comment)

            # ── Section 2: Type-specific content ──────────────────────────────
            if is_grouped:
                _render_grouped_section(detalle)
            else:
                _render_sos_section(detalle)

            # ── Section 3: Payments table (always) ────────────────────────────
            _render_payments_section(detalle)


# ── Render helpers ─────────────────────────────────────────────────────────────


def _render_sos_section(detalle: any) -> None:
    """Section 2a — SOS Records table."""
    ui.label("Historial SOS").classes("text-lg font-bold mt-6 mb-2")

    if not detalle.sos_records:
        ui.label("No hay registros SOS para esta gestión.").classes(
            "text-gray-400"
        )
        return

    with ui.row().classes(
        "items-center gap-2 py-2 border-b border-gray-600 font-bold"
    ):
        for label, width in [
            ("Gestión", "w-20"),
            ("Categoría", "w-28"),
            ("Motivo", "w-36"),
            ("Estado", "w-24"),
            ("Usuario Carga", "w-28"),
            ("Usuario Resp.", "w-28"),
            ("ITR", "w-16"),
        ]:
            ui.label(label).classes(f"text-xs {width}")

    for sc in sorted(
        detalle.sos_records, key=lambda r: r.gestion, reverse=True
    ):
        with ui.row().classes("items-center gap-2 py-1 hover:bg-gray-800"):
            ui.label(str(sc.gestion)).classes("text-sm w-20")
            ui.label(sc.category).classes("text-sm w-28")
            ui.label(sc.reason).classes("text-sm w-36")
            ui.label(sc.status).classes("text-sm w-24")
            ui.label(sc.load_user).classes("text-sm w-28")
            ui.label(sc.response_user).classes("text-sm w-28")
            ui.label(str(sc.itr)).classes("text-sm w-16")


def _render_grouped_section(detalle: any) -> None:
    """Section 2b — Grouped Data card."""
    gd = detalle.grouped_data
    ui.label("Datos del Lote").classes("text-lg font-bold mt-6 mb-2")

    with ui.card().classes("w-full p-4"):
        if gd:
            with ui.grid(columns=2).classes("gap-4"):
                _field("Referencia", gd.external_reference)
                _field("Notas", gd.notes or "—")
                _field("Fecha de creación",
                       gd.created_at.strftime("%Y-%m-%d %H:%M"))
        else:
            ui.label("No hay datos de lote para esta gestión.").classes(
                "text-gray-400"
            )


def _render_payments_section(detalle: any) -> None:
    """Section 3 — Payments table (all types) + inline creation."""
    container = Container.get_instance()

    with ui.row().classes("items-center justify-between mt-6 mb-2"):
        ui.label("Pagos").classes("text-lg font-bold")

        ui.button(
            "Nuevo Pago",
            icon="add",
            on_click=lambda: _nuevo_pago_dialog(container, detalle.claim_id),
        ).props("flat color=white size=sm")

    if not detalle.payments:
        ui.label("No hay pagos registrados para esta gestión.").classes(
            "text-gray-400"
        )
        return

    with ui.row().classes(
        "items-center gap-2 py-2 border-b border-gray-600 font-bold"
    ):
        for label, width in [
            ("Monto", "w-28"),
            ("Fecha", "w-28"),
            ("Activo", "w-16"),
        ]:
            ui.label(label).classes(f"text-xs {width}")

    for p in sorted(
        detalle.payments, key=lambda pm: pm.created_date, reverse=True
    ):
        with ui.row().classes("items-center gap-2 py-1 hover:bg-gray-800"):
            ui.label(f"${p.amount:,.2f}").classes("text-sm w-28 text-right")
            ui.label(p.created_date.strftime("%Y-%m-%d")).classes(
                "text-sm w-28 text-gray-400"
            )
            ui.label("Sí" if p.active else "No").classes("text-sm w-16")


def _nuevo_pago_dialog(container: Container, claim_id: UUID) -> None:
    """Open the create-payment dialog pre-filled with *claim_id*."""
    agent_options = {str(a.agent_id): a.name for a in container.agent_repo.get_all()}
    via_options = {str(v.payment_via_id): v.name for v in container.payment_via_repo.get_all()}
    nc_via = container.payment_via_repo.get_nc()
    nc_via_id = str(nc_via.payment_via_id) if nc_via else None
    period_options = {str(p.period_id): p.period_name
                      for p in container.listar_periodos.execute().periods}

    with ui.dialog() as dlg, ui.card():
        ui.label("Nuevo Pago").classes("text-lg font-bold mb-2")

        payer_select = ui.select(
            label="Pagador", options=agent_options, with_input=True,
        ).classes("w-full")
        payee_select = ui.select(
            label="Beneficiario", options=agent_options, with_input=True,
        ).classes("w-full")
        via_select = ui.select(
            label="Medio de Pago", options=via_options, with_input=True,
        ).classes("w-full")
        amount_input = ui.number(label="Monto", precision=2)

        period_input = ui.select(
            label="Período", options=period_options, with_input=True,
        ).classes("w-full")
        period_input.set_visibility(False)

        def _on_via_change() -> None:
            period_input.set_visibility(via_select.value == nc_via_id)
        via_select.on("update:model-value", _on_via_change)

        with ui.row().classes("gap-2 justify-end mt-2"):
            ui.button("Cancelar", on_click=dlg.close).props("flat")

            @with_audit_user
            async def _save() -> None:
                missing = []
                payer_val = payer_select.value
                payee_val = payee_select.value
                via_val = via_select.value
                amount_val = amount_input.value
                period_val = period_input.value

                if not payer_val:
                    missing.append("Pagador")
                if not payee_val:
                    missing.append("Beneficiario")
                if not via_val:
                    missing.append("Medio de Pago")
                if not amount_val or float(amount_val) <= 0:
                    missing.append("Monto")
                if via_val == nc_via_id and not period_val:
                    missing.append("Período (NC)")

                if missing:
                    ui.notify("Campos requeridos: " + ", ".join(missing), type="warning")
                    return

                try:
                    inp = RegistrarPagoInput(
                        claim_id=claim_id,
                        payer_id=UUID(payer_val),
                        payee_id=UUID(payee_val),
                        payment_via_id=UUID(via_val),
                        amount=float(amount_val),
                        period_id=UUID(period_val) if period_val else None,
                    )
                    container.registrar_pago.execute(inp)
                    ui.notify("Pago registrado", type="positive")
                    dlg.close()
                    ui.navigate.reload()
                except ValueError as e:
                    ui.notify(str(e), type="negative")
                except Exception as e:
                    ui.notify(f"Error al registrar pago: {e}", type="negative")

            ui.button("Guardar", on_click=_save)

    dlg.open()


def _field(label: str, value: str) -> None:
    """Render a labeled field inside a grid."""
    with ui.column().classes("gap-0"):
        ui.label(label).classes("text-xs text-gray-400")
        ui.label(value).classes("text-sm")
