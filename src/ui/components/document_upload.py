"""Reusable document upload component with NiceGUI drag-and-drop support."""

from collections.abc import Callable
from uuid import UUID

from nicegui import app, ui

from src.application.use_cases.documents.subir_documento import SubirDocumentoInput
from src.ui.services.audit_helper import with_audit_user


class DocumentUpload:
    """Upload widget that accepts entity context and triggers the upload use case.

    Typical usage inside a page::

        DocumentUpload(entity_type="claim", entity_id=claim_id, on_upload=refresh_list).render()
    """

    def __init__(
        self,
        entity_type: str,
        entity_id: UUID,
        on_upload: Callable[[], None] | None = None,
    ) -> None:
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._on_upload = on_upload

    def render(self) -> None:
        """Render the upload card with drag-and-drop zone."""
        from src.infrastructure.container import get_container

        with ui.card().classes("w-full p-4"):
            ui.label("Subir Documento").classes("text-lg font-semibold mb-2")

            @with_audit_user
            def handle_upload(e) -> None:
                content = e.content.read()
                name = e.name

                user_id_raw = app.storage.user.get("user_id")
                if not user_id_raw:
                    ui.notify("Usuario no autenticado", type="negative")
                    return

                container = get_container()
                try:
                    container.subir_documento.execute(
                        SubirDocumentoInput(
                            content=content,
                            name=name,
                            mime=e.type or "application/octet-stream",
                            type="documento",
                            entity_type=self._entity_type,
                            entity_id=self._entity_id,
                            uploaded_by=UUID(user_id_raw),
                        )
                    )
                    ui.notify(f"Documento subido: {name}", type="positive")
                    if self._on_upload:
                        self._on_upload()
                except Exception as ex:
                    ui.notify(f"Error: {ex}", type="negative")

            ui.upload(
                on_upload=handle_upload,
                multiple=False,
                max_file_size=50 * 1024 * 1024,  # 50 MB
            ).classes("w-full")
