"""Claim detail page — header card, type-specific Section 2, and payments table."""

from uuid import UUID

from nicegui import ui

from src.application.use_cases.claims.obtener_gestion_por_id import (
    ObtenerGestionPorIdInput,
)
from src.domain.exceptions import ClaimNotFoundError
from src.infrastructure.container import Container
from src.ui.components.shell import AppShell


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
                    _field("Grupo", detalle.group_name)
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

    for sc in detalle.sos_records:
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
    """Section 3 — Payments table (all types)."""
    ui.label("Pagos").classes("text-lg font-bold mt-6 mb-2")

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

    for p in detalle.payments:
        with ui.row().classes("items-center gap-2 py-1 hover:bg-gray-800"):
            ui.label(f"${p.amount:,.2f}").classes("text-sm w-28 text-right")
            ui.label(p.created_date.strftime("%Y-%m-%d")).classes(
                "text-sm w-28 text-gray-400"
            )
            ui.label("Sí" if p.active else "No").classes("text-sm w-16")


def _field(label: str, value: str) -> None:
    """Render a labeled field inside a grid."""
    with ui.column().classes("gap-0"):
        ui.label(label).classes("text-xs text-gray-400")
        ui.label(value).classes("text-sm")
