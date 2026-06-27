"""New claim dialog — dynamic form per claim type with type selector dispatch."""

from collections.abc import Callable
from uuid import UUID

from nicegui import ui

from src.application.use_cases.claims.registrar_gestion_sos import (
    RegistrarGestionSOSInput,
)
from src.application.use_cases.claims.registrar_grouped_claim import (
    RegistrarGroupedClaimInput,
)
from src.domain.exceptions import GestionAlreadyExistsError
from src.infrastructure.container import Container
from src.ui.services.audit_helper import with_audit_user


def nueva_gestion_dialog(on_success: Callable[[], None] | None = None) -> None:
    """Open a dialog to create a new claim.

    Args:
        on_success: Optional callback invoked after successful creation.
    """
    container = Container.get_instance()

    # ── Load dropdown data ──────────────────────────────────────────────────
    try:
        groups = container.obtener_grupos.execute()
        claim_kinds = container.obtener_claim_kinds.execute()
    except Exception as e:
        ui.notify(f"Error al cargar datos del formulario: {e}", type="negative")
        return

    kind_by_id: dict[str, str] = {
        str(k.claim_kind_id): k.name for k in claim_kinds
    }
    sos_kind_ids: set[str] = {
        str(k.claim_kind_id)
        for k in claim_kinds
        if k.name.upper() == "SOS"
    }
    grouped_kind_ids: set[str] = {
        str(k.claim_kind_id)
        for k in claim_kinds
        if k.name.upper() == "GROUPED"
    }

    selected_kind: dict[str, str | None] = {"value": None}

    with ui.dialog() as dlg, ui.card().classes("w-[600px] max-w-full"):
        ui.label("Nueva Gestión").classes("text-2xl font-bold mb-4")

        @ui.refreshable
        def _conditional_form() -> None:
            kind_id = selected_kind["value"]
            if kind_id is None:
                return

            with ui.card().classes("w-full mb-4 p-4"):
                ui.label("Datos del Reclamo").classes("text-lg font-bold mb-2")

                if kind_id not in sos_kind_ids:
                    group_input = ui.input(
                        label="Grupo",
                        autocomplete=[g.name for g in groups],
                    ).classes("w-full")
                else:
                    group_input = None

                claimer_name_input = ui.input(label="Asegurado").classes("w-full")
                policy_number_input = ui.input(label="Póliza").classes("w-full")
                plate_input = ui.input(label="Patente").classes("w-full")
                claimed_amount_input = ui.number(
                    label="Monto Reclamado", value=0.0
                ).classes("w-full")
                comment_input = ui.textarea(label="Comentario").classes("w-full")

            if kind_id in sos_kind_ids:
                _render_sos_card(kind_id, group_input, claimer_name_input,
                                 policy_number_input, plate_input,
                                 claimed_amount_input, comment_input,
                                 groups, container, dlg, on_success)
            elif kind_id in grouped_kind_ids:
                _render_grouped_card(kind_id, group_input, claimer_name_input,
                                     policy_number_input, plate_input,
                                     claimed_amount_input, comment_input,
                                     groups, container, dlg, on_success)
            else:
                ui.label(f"Tipo de gestión '{kind_by_id.get(kind_id, '')}' "
                         "no implementado").classes("text-gray-400 mt-4")

        def _on_kind_change(e) -> None:
            selected_kind["value"] = e.value
            _conditional_form.refresh()

        ui.select(
            label="Tipo de Gestión",
            options=kind_by_id,
            on_change=_on_kind_change,
        ).classes("w-full mb-4")

        _conditional_form()

    dlg.open()


# ── Helpers ────────────────────────────────────────────────────────────────────


def _resolve_group_id(group_name: str, groups: list, container: Container) -> UUID:
    group_name = group_name.strip()
    for g in groups:
        if g.name.lower() == group_name.lower():
            return g.group_id
    group = container.registrar_grupo.execute(group_name)
    return group.group_id


# ── Render helpers ─────────────────────────────────────────────────────────────


def _render_sos_card(
    kind_id: str,
    group_input: ui.input,
    claimer_name_input: ui.input,
    policy_number_input: ui.input,
    plate_input: ui.input,
    claimed_amount_input: ui.number,
    comment_input: ui.textarea,
    groups: list,
    container: Container,
    dialog: ui.dialog,
    on_success: Callable[[], None] | None,
) -> None:
    with ui.card().classes("w-full mb-4 p-4"):
        ui.label("Datos SOS").classes("text-lg font-bold mb-2")

        gestion_input = ui.number(label="Gestión N°", value=0).classes("w-full")
        category_input = ui.input(label="Categoría").classes("w-full")
        reason_input = ui.input(label="Motivo").classes("w-full")
        load_user_input = ui.input(label="Usuario Carga").classes("w-full")
        response_user_input = ui.input(label="Usuario Respuesta").classes("w-full")
        status_select = ui.select(
            label="Estado",
            options=["ABIERTO", "CERRADO", "RECHAZADO"],
        ).classes("w-full")
        itr_input = ui.number(label="ITR", value=0).classes("w-full")

    @with_audit_user
    def _on_submit() -> None:
        if not claimer_name_input.value:
            ui.notify("El nombre del asegurado es requerido", type="warning")
            return
        if not policy_number_input.value:
            ui.notify("El número de póliza es requerido", type="warning")
            return
        if not plate_input.value or len(plate_input.value.strip()) < 6:
            ui.notify("La patente es requerida", type="warning")
            return
        if not gestion_input.value or gestion_input.value <= 0:
            ui.notify("El número de gestión es requerido", type="warning")
            return
        if not status_select.value:
            ui.notify("Debe seleccionar un estado", type="warning")
            return

        input_data = RegistrarGestionSOSInput(
            claim_kind_id=UUID(kind_id),
            claimer_name=claimer_name_input.value.strip(),
            policy_number=policy_number_input.value.strip(),
            plate=plate_input.value.strip(),
            claimed_amount=claimed_amount_input.value or 0.0,
            comment=comment_input.value or "",
            gestion=int(gestion_input.value),
            category=category_input.value or "",
            reason=reason_input.value or "",
            load_user=load_user_input.value or "",
            response_user=response_user_input.value or "",
            status=status_select.value,
            itr=int(itr_input.value or 0),
        )

        try:
            container.registrar_gestion_sos.execute(input_data)
            ui.notify("Gestión registrada correctamente", type="positive")
            dialog.close()
            if on_success:
                on_success()
        except GestionAlreadyExistsError as e:
            ui.notify(str(e), type="negative")
        except Exception as e:
            ui.notify(f"Error al registrar gestión: {e}", type="negative")

    ui.button(
        "Registrar Gestión",
        on_click=_on_submit,
        icon="save",
    ).props("color=primary")


def _render_grouped_card(
    kind_id: str,
    group_input: ui.input,
    claimer_name_input: ui.input,
    policy_number_input: ui.input,
    plate_input: ui.input,
    claimed_amount_input: ui.number,
    comment_input: ui.textarea,
    groups: list,
    container: Container,
    dialog: ui.dialog,
    on_success: Callable[[], None] | None,
) -> None:
    with ui.card().classes("w-full mb-4 p-4"):
        ui.label("Datos del Lote").classes("text-lg font-bold mb-2")

        group_claim_select = ui.select(
            label="Lote",
            options={str(g.group_id): (g.external_reference or g.name)
                     for g in groups},
            with_input=True,
        ).classes("w-full")

        notes_input = ui.textarea(label="Notas").classes("w-full")

    @with_audit_user
    def _on_submit() -> None:
        group_name = group_input.value.strip() if group_input.value else ""
        if not group_name:
            ui.notify("Debe ingresar un grupo", type="warning")
            return
        if not claimer_name_input.value:
            ui.notify("El nombre del asegurado es requerido", type="warning")
            return
        if not policy_number_input.value:
            ui.notify("El número de póliza es requerido", type="warning")
            return
        if not plate_input.value or len(plate_input.value.strip()) < 6:
            ui.notify("La patente es requerida", type="warning")
            return
        if not group_claim_select.value:
            ui.notify("Debe seleccionar un lote", type="warning")
            return

        try:
            group_id = _resolve_group_id(group_name, groups, container)
        except Exception as e:
            ui.notify(f"Error al crear/buscar el grupo: {e}", type="negative")
            return

        input_data = RegistrarGroupedClaimInput(
            claim_kind_id=UUID(kind_id),
            group_id=group_id,
            claimer_name=claimer_name_input.value.strip(),
            policy_number=policy_number_input.value.strip(),
            plate=plate_input.value.strip(),
            claimed_amount=claimed_amount_input.value or 0.0,
            comment=comment_input.value or "",
            group_claim_id=UUID(group_claim_select.value),
            notes=notes_input.value or "",
        )

        try:
            container.registrar_grouped_claim.execute(input_data)
            ui.notify("Gestión registrada correctamente", type="positive")
            dialog.close()
            if on_success:
                on_success()
        except Exception as e:
            ui.notify(f"Error al registrar gestión: {e}", type="negative")

    ui.button(
        "Registrar Gestión",
        on_click=_on_submit,
        icon="save",
    ).props("color=primary")
