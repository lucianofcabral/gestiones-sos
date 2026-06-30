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
                """Render the related-entities table for a selected document using ui.table()."""
                ui.label("Entidades Relacionadas").classes(
                    "text-lg font-semibold mb-2 mt-4"
                )

                # Define table columns for related entities
                entity_columns = [
                    {'name': 'documento', 'label': 'Documento', 'field': 'documento', 'align': 'left', 'sortable': True, 'style': 'min-width: 150px;'},
                    {'name': 'tipo', 'label': 'Tipo', 'field': 'tipo', 'align': 'left', 'sortable': True, 'style': 'min-width: 100px;'},
                    {'name': 'categoria', 'label': 'Categoría', 'field': 'categoria', 'align': 'left', 'sortable': True, 'style': 'min-width: 100px;'},
                    {'name': 'fecha', 'label': 'Fecha', 'field': 'fecha', 'align': 'left', 'sortable': True, 'style': 'min-width: 100px;'},
                    {'name': 'detalle', 'label': 'Detalle', 'field': 'detalle', 'align': 'left', 'sortable': False, 'style': 'flex: 1; min-width: 200px;'},
                ]

                # Prepare table data
                table_rows = []
                for ent in ents:
                    etype = ent["entity_type"]
                    doc = _container.document_repo.get_by_id(ent["document_id"])
                    created = ent.get("created_at")
                    fecha_str = created.strftime("%d/%m/%Y") if created and hasattr(created, "strftime") else "—"
                    
                    table_rows.append({
                        'id': str(ent["document_id"]),
                        'document_id': ent["document_id"],
                        'entity_id': ent["entity_id"],
                        'entity_type': etype,
                        'documento': doc.name if doc else "—",
                        'tipo': _ENTITY_TYPE_LABELS.get(etype, etype),
                        'categoria': _CATEGORY_LABELS.get(etype, etype),
                        'fecha': fecha_str,
                        'detalle': ent.get("display", "—"),
                    })

                # Create table
                if table_rows:
                    table = ui.table(columns=entity_columns, rows=table_rows, row_key='id').classes('w-full')
                    
                    # Register click handler for row selection
                    def _handle_row_click(ent: dict) -> None:
                        _open_entity(ent)
                    
                    # Bind table row click
                    # Note: Using custom click handler via JavaScript slot
                    table.add_slot('body-cell-documento', '''
                        <q-td :props="props" class="cursor-pointer hover:bg-gray-700 rounded" @click="$parent.$emit('row-select', props.row)">
                            {{ props.row.documento }}
                        </q-td>
                    ''')
                    table.on('row-select', lambda e: _handle_row_click(e.args))

            # ── List view ─────────────────────────────────────────────────
            def _render_list_view(docs: list) -> None:
                # Define columns for list view
                list_columns = [
                    {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre', 'align': 'left', 'sortable': True, 'style': 'min-width: 200px; flex: 1;'},
                    {'name': 'tipo', 'label': 'Tipo', 'field': 'tipo', 'align': 'left', 'sortable': True, 'style': 'min-width: 100px;'},
                    {'name': 'tamaño', 'label': 'Tamaño', 'field': 'tamaño', 'align': 'right', 'sortable': True, 'style': 'min-width: 100px;'},
                    {'name': 'mime', 'label': 'MIME', 'field': 'mime', 'align': 'left', 'sortable': True, 'style': 'min-width: 120px;'},
                    {'name': 'fecha', 'label': 'Fecha', 'field': 'fecha', 'align': 'left', 'sortable': True, 'style': 'min-width: 100px;'},
                    {'name': 'acciones', 'label': 'Acciones', 'field': 'acciones', 'align': 'center', 'sortable': False, 'style': 'min-width: 80px;'},
                ]

                # Prepare table data
                table_rows = []
                sorted_docs = sorted(docs, key=lambda d: d.created_at, reverse=True)
                for doc in sorted_docs:
                    table_rows.append({
                        'id': str(doc.document_id),
                        'document_id': doc.document_id,
                        'nombre': doc.name,
                        'tipo': doc.type,
                        'tamaño': _format_size(doc.size),
                        'mime': doc.mime,
                        'fecha': doc.created_at.strftime("%d/%m/%Y"),
                        'is_selected': selected_doc_id["id"] == doc.document_id,
                    })

                if table_rows:
                    table = ui.table(columns=list_columns, rows=table_rows, row_key='id').classes('w-full')
                    
                    # Add action icons slot
                    table.add_slot('body-cell-acciones', '''
                        <q-td :props="props" class="text-center">
                            <q-btn icon="download" @click="$parent.$emit('download', props.row)" flat dense color="blue" size="sm" />
                        </q-td>
                    ''')
                    
                    # Register handlers
                    def _handle_download(row: dict) -> None:
                        _download(row.get('document_id'))
                    
                    table.on('download', lambda e: _handle_download(e.args))

            # ── Category view ────────────────────────────────────────────
            def _render_category_view(docs: list) -> None:
                categories = _group_docs_by_category(docs, container)

                # Define columns for category view (simpler than list view)
                cat_columns = [
                    {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre', 'align': 'left', 'sortable': True, 'style': 'flex: 1; min-width: 150px;'},
                    {'name': 'tipo', 'label': 'Tipo', 'field': 'tipo', 'align': 'left', 'sortable': True, 'style': 'min-width: 80px;'},
                    {'name': 'fecha', 'label': 'Fecha', 'field': 'fecha', 'align': 'left', 'sortable': True, 'style': 'min-width: 100px;'},
                    {'name': 'acciones', 'label': 'Acciones', 'field': 'acciones', 'align': 'center', 'sortable': False, 'style': 'min-width: 80px;'},
                ]

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
                        # Prepare table data for this category
                        table_rows = []
                        sorted_cat_docs = sorted(
                            docs_in_cat,
                            key=lambda d: d.created_at,
                            reverse=True,
                        )
                        for doc in sorted_cat_docs:
                            table_rows.append({
                                'id': str(doc.document_id),
                                'document_id': doc.document_id,
                                'nombre': doc.name,
                                'tipo': doc.type,
                                'fecha': doc.created_at.strftime("%d/%m/%Y"),
                                'is_selected': selected_doc_id["id"] == doc.document_id,
                            })

                        if table_rows:
                            table = ui.table(columns=cat_columns, rows=table_rows, row_key='id').classes('w-full')
                            
                            # Add action icons slot
                            table.add_slot('body-cell-acciones', '''
                                <q-td :props="props" class="text-center">
                                    <q-btn icon="download" @click="$parent.$emit('download', props.row)" flat dense color="blue" size="sm" />
                                </q-td>
                            ''')
                            
                            # Register handlers
                            def _handle_download_cat(row: dict) -> None:
                                _download(row.get('document_id'))
                            
                            table.on('download', lambda e: _handle_download_cat(e.args))

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
