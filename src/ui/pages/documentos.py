"""Document gallery page and download endpoint."""

import tempfile
import pathlib
from uuid import UUID

from nicegui import app, ui

from src.infrastructure.container import get_container
from src.ui.components.shell import AppShell

# ── Category constants ─────────────────────────────────────────────────────────

_CATEGORY_ICONS: dict[str, str] = {
    "claim": "assignment",
    "invoice": "receipt",
    "group_claim": "group",
}

_CATEGORY_LABELS: dict[str, str] = {
    "claim": "Gestiones",
    "invoice": "Facturas",
    "group_claim": "Grupos",
}

_ENTITY_TYPE_LABELS: dict[str, str] = {
    "claim": "Gestión",
    "invoice": "Factura",
    "group_claim": "Grupo",
}

_CATEGORY_COLORS: dict[str, str] = {
    "claim": "#1a5276",      # dark blue
    "invoice": "#1e8449",    # dark green
    "group_claim": "#7d3c98",  # dark purple
}

# ── Entity enrichment ──────────────────────────────────────────────────────────


def _enrich_entities(doc_entities: list[dict], container) -> list[dict]:
    """Enrich document_entities rows with actual entity data."""
    enriched = []
    for ent in doc_entities:
        entity_type = ent["entity_type"]
        entity_id = ent["entity_id"]
        enriched_row: dict = {
            "document_id": ent["document_id"],
            "entity_type": entity_type,
            "entity_id": entity_id,
            "created_at": ent.get("created_at"),
        }

        if entity_type == "claim":
            claim = container.claim_repo.get_by_id(entity_id)
            if claim:
                sos_claims = container.sos_claim_repo.get_claims_by_claim_id(
                    entity_id
                )
                sos = sos_claims[0] if sos_claims else None
                enriched_row["entity"] = claim
                enriched_row["sos_claim"] = sos

                # Resolve claim kind name
                kind_name = "—"
                if claim.claim_kind_id:
                    kind = container.claim_kind_repo.get_by_id(claim.claim_kind_id)
                    if kind:
                        kind_name = kind.name

                enriched_row["display"] = (
                    f"Tipo: {kind_name} | "
                    f"Nro.: {sos.gestion if sos else '—'} | "
                    f"Dominio: {claim.plate} | "
                    f"Póliza: {claim.policy_number} | "
                    f"Cliente: {claim.claimer_name}"
                )

        elif entity_type == "invoice":
            invoice = container.billing_repo.get_by_id(entity_id)
            if invoice:
                period = container.period_repo.get_by_id(invoice.period_id)
                period_name = (
                    period.period_name if period else f"ID: {invoice.period_id}"
                )
                enriched_row["entity"] = invoice
                enriched_row["display"] = (
                    f"Nro. Factura: {invoice.invoice_number} | "
                    f"Período {period_name}"
                )

        elif entity_type == "group_claim":
            group = container.group_claim_repo.get_by_id(entity_id)
            if group:
                all_claims = container.claim_repo.get_all()
                count = sum(
                    1 for c in all_claims if c.group_id == group.group_id
                )
                enriched_row["entity"] = group
                enriched_row["display"] = (
                    f"Nombre: {group.name} | "
                    f"Cant. Gestiones: {count}"
                )

        enriched.append(enriched_row)

    return enriched


# ── Category grouping ──────────────────────────────────────────────────────────


def _group_docs_by_category(
    docs: list, container,
) -> dict[str, list]:
    """Group documents by entity type. Each doc can appear in multiple categories."""
    categories: dict[str, list] = {
        "claim": [],
        "invoice": [],
        "group_claim": [],
    }

    for doc in docs:
        entities = container.document_repo.get_document_entities(doc.document_id)
        seen_cats: set[str] = set()
        for ent in entities:
            etype = ent["entity_type"]
            if etype in categories and etype not in seen_cats:
                categories[etype].append(doc)
                seen_cats.add(etype)

    return categories


# ── Entity navigation dispatch ─────────────────────────────────────────────────


def _open_entity(enriched_ent: dict) -> None:
    """Open the appropriate dialog/navigation for the entity."""
    entity_type = enriched_ent["entity_type"]
    entity_id = enriched_ent["entity_id"]
    entity = enriched_ent.get("entity")

    if entity_type == "claim":
        app.storage.user["return_to"] = "/documentos"
        ui.navigate.to(f"/gestiones/{entity_id}")

    elif entity_type == "invoice":
        from src.ui.pages.facturacion import _invoice_dialog

        _invoice_dialog(
            invoice=entity,
            refresh_fn=lambda: None,
            existing_dialog=None,
        )

    elif entity_type == "group_claim":
        from src.ui.pages.grupos import edit_group_dialog
        from src.infrastructure.container import Container

        edit_group_dialog(
            group=entity,
            container=Container.get_instance(),
            refresh_fn=lambda: None,
        )


# ── Page registration ──────────────────────────────────────────────────────────


def register_documentos_page() -> None:
    """Register the gallery page at /documentos and the download endpoint."""

    # ── Gallery page ──────────────────────────────────────────────────────────
    @ui.page("/documentos")
    def documentos_page() -> None:
        with AppShell():
            ui.label("Documentos").classes("text-2xl font-bold mb-4")

            container = get_container()

            # ── State (mutable containers for NiceGUI closures) ────────────────
            selected_doc_id: dict[str, UUID | None] = {"id": None}
            selected_doc_entities: dict[str, list] = {"data": []}
            view_mode: dict[str, str] = {"mode": "list"}

            # ── Toggle ─────────────────────────────────────────────────────────
            view_toggle = ui.toggle(
                {"list": "Lista", "categories": "Categorías"},
                value="list",
            )

            def _on_view_change() -> None:
                view_mode["mode"] = view_toggle.value
                _render_all.refresh()

            view_toggle.on("update:model-value", _on_view_change)

            # ── Actions ────────────────────────────────────────────────────────
            def _select_document(doc_id: UUID) -> None:
                if selected_doc_id["id"] == doc_id:
                    # Deselect
                    selected_doc_id["id"] = None
                    selected_doc_entities["data"] = []
                else:
                    selected_doc_id["id"] = doc_id
                    raw = container.document_repo.get_document_entities(doc_id)
                    selected_doc_entities["data"] = _enrich_entities(
                        raw, container
                    )
                _render_all.refresh()

            def _download(doc_id: UUID) -> None:
                ui.navigate.to(f"/api/documents/{doc_id}/file")

            # ── Render ─────────────────────────────────────────────────────────
            @ui.refreshable
            def _render_all() -> None:
                # ── Related entities table (top, when a doc is selected) ──
                sid = selected_doc_id["id"]
                if sid is not None:
                    ents = selected_doc_entities["data"]
                    if ents:
                        _render_related_entities(ents, container)

                docs = container.document_repo.get_all()

                if not docs:
                    ui.label("No hay documentos cargados.").classes(
                        "text-gray-400 italic"
                    )
                    return

                if view_mode["mode"] == "list":
                    _render_list_view(docs)
                else:
                    _render_category_view(docs)

            # ── Related entities table ─────────────────────────────────────
            def _render_related_entities(ents: list[dict], _container) -> None:
                """Render the related-entities table for a selected document."""
                ui.label("Entidades Relacionadas").classes(
                    "text-lg font-semibold mb-2 mt-4"
                )

                _entity_columns = [
                    ("Documento", "text-sm w-36"),
                    ("Tipo", "text-sm w-24"),
                    ("Categoría", "text-sm w-24"),
                    ("Fecha", "text-sm w-24"),
                    ("Detalle", "text-sm flex-1"),
                ]

                with ui.row().classes(
                    "items-center gap-2 py-2 border-b border-gray-600 font-bold"
                ):
                    for label, cls in _entity_columns:
                        ui.label(label).classes(cls)

                for ent in ents:
                    etype = ent["entity_type"]
                    bg_color = _CATEGORY_COLORS.get(etype, "#555")

                    with ui.row().classes(
                        "items-center gap-2 py-2 hover:bg-gray-700 "
                        "cursor-pointer rounded"
                    ).on("click", lambda e=ent: _open_entity(e)):
                        # Document name
                        doc = _container.document_repo.get_by_id(
                            ent["document_id"]
                        )
                        ui.label(doc.name if doc else "—").classes(
                            "text-sm w-36"
                        )

                        # Entity type (Gestión, Factura, Grupo)
                        ui.label(_ENTITY_TYPE_LABELS.get(etype, etype)).classes(
                            "text-sm w-24"
                        )

                        # Category badge
                        ui.label(
                            _CATEGORY_LABELS.get(etype, etype)
                        ).classes(
                            "text-xs font-bold px-2 py-1 rounded text-white "
                            "text-center w-24"
                        ).style(f"background-color: {bg_color}")

                        # Date
                        created = ent.get("created_at")
                        if created and hasattr(created, "strftime"):
                            ui.label(created.strftime("%d/%m/%Y")).classes(
                                "text-sm w-24 text-gray-400"
                            )
                        else:
                            ui.label("—").classes(
                                "text-sm w-24 text-gray-400"
                            )

                        # Detail (category-specific)
                        ui.label(ent.get("display", "—")).classes(
                            "text-sm flex-1 text-gray-300"
                        )

            # ── List view ─────────────────────────────────────────────────
            def _render_list_view(docs: list) -> None:
                list_columns = [
                    ("Nombre", "text-sm w-36"),
                    ("Tipo", "text-sm w-20"),
                    ("Tamaño", "text-sm w-20 text-right"),
                    ("MIME", "text-sm w-28"),
                    ("Fecha", "text-sm w-24"),
                    ("", "text-sm w-16"),
                ]
                with ui.row().classes(
                    "items-center gap-2 py-2 border-b border-gray-600 "
                    "font-bold w-full"
                ):
                    for label, cls in list_columns:
                        ui.label(label).classes(cls)

                for doc in sorted(
                    docs, key=lambda d: d.created_at, reverse=True
                ):
                    is_selected = (
                        selected_doc_id["id"] == doc.document_id
                    )
                    row_cls = (
                        "items-center gap-2 py-2 px-3 cursor-pointer rounded "
                        f"{'bg-blue-900' if is_selected else 'hover:bg-gray-700'}"
                    )
                    with ui.row().classes(row_cls).on(
                        "click",
                        lambda d=doc: _select_document(d.document_id),
                    ):
                        ui.label(doc.name).classes("text-sm w-36 truncate")
                        ui.label(doc.type).classes("text-sm w-20")
                        ui.label(_format_size(doc.size)).classes(
                            "text-sm w-20 text-right text-gray-400"
                        )
                        ui.label(doc.mime).classes(
                            "text-sm w-28 text-gray-400 truncate"
                        )
                        ui.label(
                            doc.created_at.strftime("%d/%m/%Y")
                        ).classes("text-sm w-24 text-gray-400")
                        ui.button(
                            icon="download",
                            on_click=lambda did=doc.document_id: _download(
                                did
                            ),
                        ).props("flat dense round size=sm")

            # ── Category view ────────────────────────────────────────────
            def _render_category_view(docs: list) -> None:
                categories = _group_docs_by_category(docs, container)

                for etype in ("claim", "invoice", "group_claim"):
                    docs_in_cat = categories[etype]
                    cat_label = _CATEGORY_LABELS[etype]

                    if not docs_in_cat:
                        ui.label(
                            f"{cat_label}: sin documentos vinculados."
                        ).classes("text-gray-500 italic text-sm mb-2")
                        continue

                    with ui.expansion(
                        text=f"{cat_label} ({len(docs_in_cat)})",
                        icon=_CATEGORY_ICONS[etype],
                    ).classes("w-full bg-gray-800 rounded-lg mb-2"):
                        for doc in sorted(
                            docs_in_cat,
                            key=lambda d: d.created_at,
                            reverse=True,
                        ):
                            is_selected = (
                                selected_doc_id["id"] == doc.document_id
                            )
                            row_cls = (
                                "items-center gap-2 py-2 px-3 "
                                "cursor-pointer rounded "
                                f"{'bg-blue-900' if is_selected else 'hover:bg-gray-700'}"
                            )
                            with ui.row().classes(row_cls).on(
                                "click",
                                lambda d=doc: _select_document(
                                    d.document_id
                                ),
                            ):
                                ui.label(doc.name).classes(
                                    "text-sm flex-1 truncate"
                                )
                                ui.label(doc.type).classes(
                                    "text-xs text-gray-400 w-20"
                                )
                                ui.label(
                                    doc.created_at.strftime("%d/%m/%Y")
                                ).classes("text-xs text-gray-400 w-24")
                                ui.button(
                                    icon="download",
                                    on_click=lambda did=doc.document_id: _download(
                                        did
                                    ),
                                ).props("flat dense round size=sm")

            # ── Initial render ────────────────────────────────────────────────
            _render_all()

    # ── Download endpoint ─────────────────────────────────────────────────────
    @ui.page("/api/documents/{document_id:str}/file")
    def download_documento(document_id: str) -> None:
        if "token" not in app.storage.user:
            ui.navigate.to("/login")
            return

        try:
            doc_uuid = UUID(document_id)
        except ValueError:
            ui.label("ID de documento inválido").classes("text-red-500")
            return

        container = get_container()
        try:
            result = container.descargar_documento.execute(doc_uuid)
        except FileNotFoundError:
            ui.label("Archivo no encontrado en el servidor").classes(
                "text-red-500"
            )
            return

        if result is None:
            ui.label("Documento no encontrado").classes("text-red-500")
            return

        doc = result.document
        ext = doc.name.rsplit(".", 1)[-1] if "." in doc.name else ""
        tmp = (
            pathlib.Path(tempfile.gettempdir())
            / f"doc_{doc.document_id}.{ext}"
        )
        tmp.write_bytes(result.content)
        ui.download(tmp.as_posix(), filename=doc.name)


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
