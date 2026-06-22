"""Document gallery page and download endpoint."""

import tempfile
import pathlib
from uuid import UUID

from nicegui import app, ui

from src.infrastructure.container import get_container
from src.ui.components.shell import AppShell


def register_documentos_page() -> None:
    """Register the gallery page at /documentos and the download endpoint."""

    # ── Gallery page ──────────────────────────────────────────────────────────
    @ui.page("/documentos")
    def documentos_page() -> None:
        with AppShell():
            ui.label("Documentos").classes("text-2xl font-bold mb-4")

            container = get_container()
            docs = container.document_repo.get_all()

            if docs:
                columns = [
                    {
                        "name": "name",
                        "label": "Nombre",
                        "field": "name",
                        "align": "left",
                        "sortable": True,
                    },
                    {
                        "name": "type",
                        "label": "Tipo",
                        "field": "type",
                        "align": "left",
                    },
                    {
                        "name": "size",
                        "label": "Tamaño",
                        "field": "size",
                        "align": "right",
                    },
                    {
                        "name": "mime",
                        "label": "MIME",
                        "field": "mime",
                        "align": "left",
                    },
                    {
                        "name": "date",
                        "label": "Fecha",
                        "field": "date",
                        "align": "left",
                    },
                    {
                        "name": "actions",
                        "label": "",
                        "field": "actions",
                        "align": "center",
                    },
                ]
                rows = []
                for doc in sorted(docs, key=lambda d: d.created_at, reverse=True):
                    rows.append(
                        {
                            "name": doc.name,
                            "type": doc.type,
                            "size": _format_size(doc.size),
                            "mime": doc.mime,
                            "date": doc.created_at.strftime("%d/%m/%Y"),
                            "document_id": str(doc.document_id),
                        }
                    )

                table = ui.table(
                    columns=columns, rows=rows, row_key="document_id"
                ).classes("w-full")

                table.add_slot(
                    "body-cell-actions",
                    r"""
                    <q-btn
                        size="sm"
                        flat
                        round
                        icon="download"
                        @click="$parent.$emit('download', props.row.document_id)"
                    />
                    """,
                )

                def handle_download(e) -> None:
                    doc_id = e.args
                    ui.navigate.to(f"/api/documents/{doc_id}/file")

                table.on("download", handle_download)
            else:
                ui.label("No hay documentos cargados.").classes("text-gray-400 italic")

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
            ui.label("Archivo no encontrado en el servidor").classes("text-red-500")
            return

        if result is None:
            ui.label("Documento no encontrado").classes("text-red-500")
            return

        doc = result.document
        ext = doc.name.rsplit(".", 1)[-1] if "." in doc.name else ""
        tmp = pathlib.Path(tempfile.gettempdir()) / f"doc_{doc.document_id}.{ext}"
        tmp.write_bytes(result.content)
        ui.download(tmp.as_posix(), filename=doc.name)


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
