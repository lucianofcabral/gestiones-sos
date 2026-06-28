"""Gestiones list page — sortable, paginated table with compact filters."""

import math
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
from src.ui.pages.gestiones_nueva import nueva_gestion_dialog
from src.ui.pages.sos_import import importar_gestiones_dialog
from src.ui.services.audit_helper import with_audit_user

_PAGE_SIZE = 12


def _prepare_gestiones_data(container: Container) -> list[dict]:
    """
    Prepare gestiones table data by pre-computing all lookups in one pass.
    
    Returns list of dicts with fields:
        id, claim_id, tipo, gestion, asegurado, poliza, patente, monto,
        fecha, resuelto, cant_pagos, active, has_group, has_nc, solved
    
    Complexity: O(N) where N = number of claims (one pass per repository).
    """
    # Fetch all claims
    all_claims = container.claim_repo.get_all()
    if not all_claims:
        return []
    
    # Pre-fetch all claim kinds
    all_kinds = {k.claim_kind_id: k.name for k in container.claim_kind_repo.get_all()}
    
    # Pre-compute SOS data (gestion numbers)
    sos_map = {}
    for sos in container.sos_claim_repo.get_all():
        sos_map[sos.claim_id] = sos
    
    # Pre-compute payment counts and NC flags (avoid N+1)
    payment_counts = {}
    has_nc_map = {}
    
    all_payments = container.payment_repo.get_all()
    for claim in all_claims:
        claim_payments = [p for p in all_payments if p.claim_id == claim.claim_id]
        payment_counts[claim.claim_id] = len(claim_payments)
        
        # Check if any payment has an associated NC
        has_nc = False
        for payment in claim_payments:
            try:
                nc = container.obtener_ncs.get_by_payment_id(payment.payment_id)
                if nc is not None:
                    has_nc = True
                    break
            except Exception:
                pass
        has_nc_map[claim.claim_id] = has_nc
    
    # Build rows
    rows = []
    for claim in all_claims:
        sos = sos_map.get(claim.claim_id)
        
        row = {
            'id': str(claim.claim_id),
            'claim_id': claim.claim_id,
            'tipo': all_kinds.get(claim.claim_kind_id, '—'),
            'gestion': sos.gestion if sos else '—',
            'asegurado': claim.claimer_name,
            'poliza': claim.policy_number,
            'patente': claim.plate,
            'monto': f'{claim.claimed_amount:,.2f}',
            'fecha': claim.created_at.strftime('%d/%m/%Y'),
            'resuelto': '✓' if claim.solved else '—',
            'cant_pagos': payment_counts[claim.claim_id],
            'active': claim.active,
            'has_group': claim.group_id is not None,
            'has_nc': has_nc_map[claim.claim_id],
            'solved': claim.solved,
        }
        rows.append(row)
    
    return rows


def register_gestiones_page() -> None:
    @ui.page("/gestiones")
    def gestiones_page() -> None:
        with AppShell():
            container = Container.get_instance()

            ui.label("Gestiones").classes("text-2xl font-bold")

            # ── Action buttons ─────────────────────────────────────────────────
            with ui.row().classes("items-center gap-2 mt-2"):
                ui.button(
                    "Nueva Gestión",
                    icon="add",
                    on_click=lambda: nueva_gestion_dialog(
                        on_success=lambda: _render_gestiones.refresh()
                    ),
                ).props("flat color=white")
                ui.button(
                    "Importar",
                    icon="cloud_upload",
                    on_click=lambda: importar_gestiones_dialog(
                        on_success=lambda: _render_gestiones.refresh()
                    ),
                ).props("flat color=white")

            # ── Filters ────────────────────────────────────────────────────────
            kind_options = _get_kind_options(container)

            with ui.card().classes("w-full p-3 mt-2"):
                with ui.row().classes("items-center gap-3 w-full"):
                    filter_kind = ui.select(
                        label="Tipo", options=kind_options,
                        with_input=True, clearable=True,
                    ).classes("w-36")
                    filter_text = ui.input(
                        label="Buscar",
                        placeholder="Cliente, dominio, N° gestión, póliza...",
                    ).props("dense outlined").classes("flex-1 min-w-[200px]")
                    toggle = ui.switch("Mostrar inactivos", value=False)

                with ui.row().classes("items-center gap-4 mt-1"):
                    filter_solved = ui.checkbox("Resuelta")
                    filter_has_payments = ui.checkbox("Tiene pagos")
                    filter_no_payments = ui.checkbox("No tiene pagos")
                    filter_has_nc = ui.checkbox("Tiene NC")
                    filter_no_nc = ui.checkbox("No tiene NC")

            for f in [filter_kind, filter_text, filter_solved,
                      filter_has_payments, filter_no_payments,
                      filter_has_nc, filter_no_nc, toggle]:
                f.on("update:model-value", lambda: (_reset_page(), _render_gestiones.refresh()))

            # ── Sorting & pagination state ────────────────────────────────────
            _sort_col = 0
            _sort_dir = 1
            _page = 1

            def _reset_page() -> None:
                nonlocal _page
                _page = 1

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
                nonlocal _sort_col, _sort_dir, _page
                show_inactive = toggle.value
                try:
                    result = container.obtener_gestiones.execute(
                        ObtenerGestionesInput(include_inactive=show_inactive)
                    )
                except Exception as e:
                    ui.notify(f"Error al cargar gestiones: {e}", type="negative")
                    return

                gestiones = result.gestiones

                # Pre-compute payment/NC lookups for filtering
                all_payments = container.payment_repo.get_all()
                claims_with_payments: set[UUID] = {p.claim_id for p in all_payments}
                claims_with_nc: set[UUID] = set()
                for p in all_payments:
                    nc = container.obtener_ncs.get_by_payment_id(p.payment_id)
                    if nc is not None:
                        claims_with_nc.add(p.claim_id)

                # ── Apply filters ─────────────────────────────────────────
                kind_val = filter_kind.value
                text_val = (filter_text.value or "").strip().lower()
                solved_only = filter_solved.value
                has_pay = filter_has_payments.value
                no_pay = filter_no_payments.value
                has_nc = filter_has_nc.value
                no_nc = filter_no_nc.value

                filtered = []
                for g in gestiones:
                    if kind_val and g.claim_kind_name != kind_val:
                        continue
                    if text_val:
                        haystack = (
                            f"{g.claimer_name} {g.plate} "
                            f"{g.gestion_or_reference} {g.policy_number}"
                        ).lower()
                        if text_val not in haystack:
                            continue
                    if solved_only and not g.solved:
                        continue
                    has_p = g.claim_id in claims_with_payments
                    if has_pay and not has_p:
                        continue
                    if no_pay and has_p:
                        continue
                    has_nc_val = g.claim_id in claims_with_nc
                    if has_nc and not has_nc_val:
                        continue
                    if no_nc and has_nc_val:
                        continue
                    filtered.append(g)

                gestiones = filtered

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

                # ── Paginate ──────────────────────────────────────────────
                total = len(gestiones)
                total_pages = max(1, math.ceil(total / _PAGE_SIZE))
                if _page > total_pages:
                    _page = total_pages
                start = (_page - 1) * _PAGE_SIZE
                page_gestiones = gestiones[start: start + _PAGE_SIZE]

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
                for g in page_gestiones:
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

                # ── Pagination controls ────────────────────────────────────
                with ui.row().classes("items-center justify-center gap-4 mt-4"):
                    with ui.row().classes("items-center gap-1"):
                        prev_btn = ui.button(
                            icon="chevron_left",
                            on_click=lambda: _go_to_page(_page - 1),
                        ).props("flat dense round")
                        if _page <= 1:
                            prev_btn.classes("opacity-30 pointer-events-none")

                        ui.label(f"Página {_page} de {total_pages}").classes(
                            "text-sm text-gray-300"
                        )

                        next_btn = ui.button(
                            icon="chevron_right",
                            on_click=lambda: _go_to_page(_page + 1),
                        ).props("flat dense round")
                        if _page >= total_pages:
                            next_btn.classes("opacity-30 pointer-events-none")

                    ui.label(f"({total} gestiones)").classes(
                        "text-xs text-gray-500"
                    )

            def _go_to_page(new_page: int) -> None:
                nonlocal _page
                _page = new_page
                _render_gestiones.refresh()

            # ── Initial render ─────────────────────────────────────────────────
            _render_gestiones()


def _get_kind_options(container: Container) -> dict[str, str]:
    try:
        kinds = container.obtener_claim_kinds.execute()
        return {k.name: k.name for k in kinds}
    except Exception:
        return {}
