"""Gestiones list page — sortable table with type column and conditional display."""

from uuid import UUID

from nicegui import ui

from src.application.use_cases.claims.eliminar_gestion_sos import (
    EliminarGestionSOSInput,
)
from src.application.use_cases.claims.eliminar_grouped_claim import (
    EliminarGroupedClaimInput,
)
from src.application.use_cases.claims.obtener_gestiones import (
    ObtenerGestionesInput,
)
from src.domain.exceptions import ClaimHasActivePaymentsError, ClaimNotFoundError
from src.infrastructure.container import Container
from src.ui.components.shell import AppShell
from src.ui.services.audit_helper import with_audit_user


def register_gestiones_page() -> None:
    @ui.page("/gestiones")
    def gestiones_page() -> None:
        with AppShell():
            container = Container.get_instance()

            ui.label("Gestiones").classes("text-2xl font-bold")

            # ── Active/inactive toggle ────────────────────────────────────────
            toggle = ui.switch("Mostrar inactivos", value=False)

            def _on_toggle_change() -> None:
                _render_gestiones.refresh()

            toggle.on("update:model-value", _on_toggle_change)

            # ── Sorting state ─────────────────────────────────────────────────
            _sort_col = 0
            _sort_dir = 1
            _gest_columns = [
                ("Tipo", "w-20", lambda g: g.claim_kind_name),
                ("Gestión/Ref.", "w-24", lambda g: g.gestion_or_reference),
                ("Asegurado", "w-36", lambda g: g.claimer_name),
                ("Póliza", "w-28", lambda g: g.policy_number),
                ("Patente", "w-24", lambda g: g.plate),
                ("Monto", "w-28", lambda g: g.claimed_amount),
                ("Fecha", "w-28", lambda g: g.created_at),
                ("Resuelto", "w-16", lambda g: g.solved),
                ("", "w-10", lambda g: ""),
            ]

            def _sort(col_idx: int) -> None:
                nonlocal _sort_col, _sort_dir
                if _sort_col == col_idx:
                    _sort_dir *= -1
                else:
                    _sort_col = col_idx
                    _sort_dir = 1
                _render_gestiones.refresh()

            # ── Delete handler ────────────────────────────────────────────────
            @with_audit_user
            def _delete_gestion(claim_id: str, claim_kind_name: str,
                                dialog: ui.dialog) -> None:
                try:
                    if claim_kind_name.upper() == "SOS":
                        container.eliminar_gestion_sos.execute(
                            EliminarGestionSOSInput(claim_id=UUID(claim_id))
                        )
                    else:
                        container.eliminar_grouped_claim.execute(
                            EliminarGroupedClaimInput(claim_id=UUID(claim_id))
                        )
                    ui.notify("Gestión eliminada", type="positive")
                    _render_gestiones.refresh()
                except ClaimHasActivePaymentsError as e:
                    ui.notify(str(e), type="negative")
                except ClaimNotFoundError as e:
                    ui.notify(str(e), type="negative")
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")
                finally:
                    dialog.close()

            # ── Gestiones table ───────────────────────────────────────────────

            @ui.refreshable
            def _render_gestiones() -> None:
                show_inactive = toggle.value
                try:
                    result = container.obtener_gestiones.execute(
                        ObtenerGestionesInput(include_inactive=show_inactive)
                    )
                except Exception as e:
                    ui.notify(f"Error al cargar gestiones: {e}", type="negative")
                    return

                gestiones = result.gestiones

                if not gestiones:
                    ui.label("No se encontraron gestiones").classes(
                        "text-gray-400 mt-4"
                    )
                    return

                # Sort
                gestiones = sorted(
                    gestiones,
                    key=_gest_columns[_sort_col][2],
                    reverse=_sort_dir == -1,
                )

                # Table header
                with ui.row().classes(
                    "items-center gap-2 py-2 border-b border-gray-600 font-bold"
                ):
                    for i, (label, width, _) in enumerate(_gest_columns):
                        arrow = (
                            " ▲" if _sort_col == i and _sort_dir == 1
                            else " ▼" if _sort_col == i
                            else ""
                        )
                        ui.label(f"{label}{arrow}").classes(
                            f"text-xs {width} cursor-pointer"
                        ).on("click", lambda i=i: _sort(i))

                # Table rows
                for g in gestiones:
                    with ui.row().classes(
                        "items-center gap-2 py-1 hover:bg-gray-800 cursor-pointer"
                    ) as row:
                        row.on(
                            "click",
                            lambda cid=g.claim_id: ui.navigate.to(
                                f"/gestiones/{cid}"
                            ),
                        )

                        ui.label(g.claim_kind_name).classes("text-sm w-20")
                        ui.label(g.gestion_or_reference).classes("text-sm w-24")
                        ui.label(g.claimer_name).classes("text-sm w-36")
                        ui.label(g.policy_number).classes("text-sm w-28")
                        ui.label(g.plate).classes("text-sm w-24")
                        ui.label(f"${g.claimed_amount:,.2f}").classes(
                            "text-sm w-28 text-right"
                        )
                        ui.label(g.created_at.strftime("%Y-%m-%d")).classes(
                            "text-sm w-28 text-gray-400"
                        )
                        ui.label("Sí" if g.solved else "No").classes("text-sm w-16")

                        # Delete confirmation dialog
                        with ui.dialog() as delete_dialog:
                            with delete_dialog, ui.card():
                                ui.label("Eliminar Gestión").classes(
                                    "text-lg font-bold"
                                )
                                ui.label(
                                    f"¿Está seguro de eliminar la gestión "
                                    f"N° {g.gestion_or_reference}?"
                                )
                                with ui.row().classes("gap-2 justify-end mt-2"):
                                    ui.button(
                                        "Cancelar",
                                        on_click=delete_dialog.close,
                                    ).props("flat")
                                    ui.button(
                                        "Eliminar",
                                        on_click=lambda cid=str(g.claim_id),
                                        ckn=g.claim_kind_name,
                                        d=delete_dialog: (
                                            _delete_gestion(cid, ckn, d)
                                        ),
                                    )

                        ui.button(
                            icon="delete",
                        ).on(
                            "click",
                            delete_dialog.open,
                            js_handler="(e) => { e.stopPropagation(); emit(); }",
                        ).props("flat dense round color=negative size=sm")

            # ── Initial render ─────────────────────────────────────────────────
            _render_gestiones()
