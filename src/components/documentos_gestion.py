import os
import hashlib
import tempfile
from pathlib import Path
from nicegui import ui
from src.db.database import SQLiteDB


def crear_seccion_documentos(gestion_id: int):
    """
    Crea la sección de gestión de documentos para una gestión
    """
    database = SQLiteDB()

    # Directorio base para documentos
    docs_dir = Path("files/docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

    def calcular_hash(filepath: str) -> str:
        """Calcula el SHA256 de un archivo"""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def formatear_tamano(bytes: int) -> str:
        """Convierte bytes a formato legible"""
        for unidad in ["B", "KB", "MB", "GB"]:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unidad}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"

    async def subir_archivo(e):
        """Maneja la subida de un archivo"""
        if not hasattr(e, "file") or not e.file:
            ui.notify(
                "No se seleccionó ningún archivo", type="warning"
            )
            return

        # Obtener nombre y contenido del archivo
        nombre_archivo = e.file.name
        contenido = await e.file.read()

        if not contenido or not nombre_archivo:
            ui.notify(
                "Error al procesar el archivo", type="warning"
            )
            return

        # Guardar temporalmente el archivo subido
        with tempfile.NamedTemporaryFile(
            delete=False
        ) as tmp_file:
            tmp_file.write(contenido)
            tmp_path = tmp_file.name

        try:
            # Calcular hash
            file_hash = calcular_hash(tmp_path)
            file_size = os.path.getsize(tmp_path)

            # Detectar mime type
            mime_type = database._detectar_mime(nombre_archivo)

            # Definir ruta final (usando hash como nombre para evitar duplicados)
            extension = Path(nombre_archivo).suffix
            archivo_destino = docs_dir / f"{file_hash}{extension}"

            # Mover archivo solo si no existe
            if not archivo_destino.exists():
                os.rename(tmp_path, str(archivo_destino))
            else:
                # Si ya existe, eliminar temporal
                os.unlink(tmp_path)

            # Mostrar diálogo para metadatos
            with ui.dialog() as dialog_meta, ui.card():
                ui.label("Información del Documento").classes(
                    "text-h6"
                )
                titulo_input = (
                    ui.input("Título", value=nombre_archivo)
                    .props("outlined")
                    .classes("w-full")
                )
                desc_input = (
                    ui.textarea("Descripción (opcional)")
                    .props("outlined")
                    .classes("w-full")
                )

                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button(
                        "Cancelar",
                        on_click=lambda: (
                            dialog_meta.close(),
                            os.unlink(archivo_destino)
                            if archivo_destino.exists()
                            else None,
                        ),
                    )
                    ui.button(
                        "Guardar",
                        on_click=lambda: guardar_documento(
                            dialog_meta,
                            titulo_input.value,
                            desc_input.value,
                            nombre_archivo,
                            str(archivo_destino),
                            file_hash,
                            file_size,
                            mime_type,
                        ),
                    ).props("color=primary")

            dialog_meta.open()

        except Exception as ex:
            # Limpiar en caso de error
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            ui.notify(
                f"Error subiendo archivo: {str(ex)}",
                type="negative",
            )

    def guardar_documento(
        dialog,
        titulo,
        descripcion,
        nombre_archivo,
        ruta,
        hash,
        tamano,
        mime_type,
    ):
        """Guarda el documento en la base de datos"""
        if not titulo.strip():
            ui.notify("El título es obligatorio", type="warning")
            return

        exito, mensaje = database.crear_documento(
            gestion_id=gestion_id,
            titulo=titulo.strip(),
            nombre_archivo=nombre_archivo,
            ruta=ruta,
            hash=hash,
            tamano=tamano,
            descripcion=descripcion.strip()
            if descripcion
            else None,
            mime_type=mime_type,
        )

        if exito:
            ui.notify(mensaje, type="positive")
            dialog.close()
            cargar_documentos()
        else:
            ui.notify(mensaje, type="negative")

    def descargar_documento(doc_id: int, nombre: str):
        """Permite descargar un documento"""
        doc_info = database.obtener_ruta_documento(doc_id)
        if doc_info and os.path.exists(doc_info["ruta"]):
            ui.download(doc_info["ruta"], filename=nombre)
        else:
            ui.notify("Archivo no encontrado", type="negative")

    def confirmar_eliminar(doc_id: int, titulo: str):
        """Muestra diálogo de confirmación para eliminar"""
        with ui.dialog() as dialog_confirm, ui.card():
            ui.label(
                f"¿Desea desasociar el documento '{titulo}'?"
            )
            ui.label(
                "El archivo no será eliminado físicamente."
            ).classes("text-caption")
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button(
                    "Cancelar", on_click=dialog_confirm.close
                )
                ui.button(
                    "Desasociar",
                    on_click=lambda: eliminar_documento(
                        dialog_confirm, doc_id
                    ),
                ).props("color=negative")
        dialog_confirm.open()

    def eliminar_documento(dialog, doc_id: int):
        """Desasocia un documento de la gestión"""
        exito, mensaje = database.desasociar_documento(
            gestion_id, doc_id
        )
        if exito:
            ui.notify(mensaje, type="positive")
            dialog.close()
            cargar_documentos()
        else:
            ui.notify(mensaje, type="negative")

    def cargar_documentos():
        """Carga y muestra la tabla de documentos"""
        documentos = database.obtener_documentos_por_gestion(
            gestion_id
        )

        tabla_container.clear()
        with tabla_container:
            if not documentos:
                ui.label("No hay documentos asociados").classes(
                    "text-grey"
                )
            else:
                columnas = [
                    {
                        "name": "titulo",
                        "label": "Título",
                        "field": "titulo",
                        "align": "left",
                    },
                    {
                        "name": "nombre_archivo",
                        "label": "Archivo",
                        "field": "nombre_archivo",
                        "align": "left",
                    },
                    {
                        "name": "tamano",
                        "label": "Tamaño",
                        "field": "tamano_formato",
                        "align": "left",
                    },
                    {
                        "name": "creado_en",
                        "label": "Fecha",
                        "field": "creado_en",
                        "align": "left",
                    },
                    {
                        "name": "acciones",
                        "label": "Acciones",
                        "field": "acciones",
                        "align": "center",
                    },
                ]

                # Formatear datos
                for doc in documentos:
                    doc["tamano_formato"] = formatear_tamano(
                        doc["tamano"]
                    )

                tabla = ui.table(
                    columns=columnas,
                    rows=documentos,
                    row_key="id",
                ).classes("w-full")
                tabla.add_slot(
                    "body-cell-acciones",
                    """
                    <q-td :props="props">
                        <q-btn flat dense icon="download" color="primary" @click="$parent.$emit('descargar', props.row)" />
                        <q-btn flat dense icon="delete" color="negative" @click="$parent.$emit('eliminar', props.row)" />
                    </q-td>
                    """,
                )
                tabla.on(
                    "descargar",
                    lambda e: descargar_documento(
                        e.args["id"], e.args["nombre_archivo"]
                    ),
                )
                tabla.on(
                    "eliminar",
                    lambda e: confirmar_eliminar(
                        e.args["id"], e.args["titulo"]
                    ),
                )

    # Construir UI
    with ui.expansion("Documentos", icon="description").classes(
        "w-full"
    ):
        with ui.row().classes("w-full items-center gap-2 mb-2"):
            ui.upload(
                label="Subir Documento",
                auto_upload=True,
                on_upload=subir_archivo,
            ).props("color=primary").classes("flex-grow")

        tabla_container = ui.column().classes("w-full")
        cargar_documentos()
