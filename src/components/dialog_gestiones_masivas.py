"""Dialog para agregar múltiples gestiones al mismo tiempo"""

from __future__ import annotations

import os
import hashlib
import tempfile
from pathlib import Path
from datetime import date
from nicegui import ui
from src.db.connection import get_database
from src.components.tipo_select import crear_tipo_select
from src.components.estado_select import crear_estado_select


def crear_dialog_gestiones_masivas(
    refresh_callback=None, gestiones_existentes=None
):
    """
    Crea un dialog para agregar o editar múltiples gestiones al mismo tiempo.

    Args:
        refresh_callback: Función a llamar cuando se creen/actualicen las gestiones
        gestiones_existentes: Lista de gestiones existentes para editar (modo edición)

    Returns:
        ui.dialog: El dialog creado (sin abrir)
    """
    database = get_database()

    # Modo edición si se proporcionan gestiones existentes
    es_modo_edicion = (
        gestiones_existentes is not None
        and len(gestiones_existentes) > 0
    )

    # Directorio base para documentos
    docs_dir = Path("files/docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Estado local
    if es_modo_edicion:
        # Cargar gestiones existentes en el formato interno
        gestiones_data = [
            {
                "id": g["id"],
                "fecha": g["fecha"],
                "cliente": g["cliente"],
                "dominio": g["dominio"],
                "poliza": g["poliza"],
                "tipo": g["tipo"],
                "motivo": g["motivo"],
                "ncaso": g["ncaso"],
                "usuariocarga": g["usuariocarga"],
                "usuariorespuesta": g["usuariorespuesta"],
                "estado": g["estado"],
                "itr": g["itr"],
                "totalfactura": g["totalfactura"],
                "terminado": g["terminado"],
                "obs": g["obs"],
                "activa": g["activa"],
            }
            for g in gestiones_existentes
        ]
    else:
        gestiones_data = []

    documentos_pendientes = []

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

    with (
        ui.dialog() as dialog,
        ui.card().classes(
            "w-full max-w-6xl max-h-[90vh] overflow-auto"
        ),
    ):
        # Encabezado
        with ui.row().classes(
            "w-full items-center bg-blue-100 dark:bg-blue-900/30 p-4 rounded-lg"
        ):
            icono = "edit" if es_modo_edicion else "playlist_add"
            ui.icon(icono, size="3rem").classes("text-blue-600")

            with ui.column().classes("flex-1 gap-1 ml-4"):
                titulo = (
                    "Editar Gestiones Relacionadas"
                    if es_modo_edicion
                    else "Agregar Múltiples Gestiones"
                )
                ui.label(titulo).classes("text-h5 font-bold")
                descripcion = (
                    "Edita gestiones que comparten documentos"
                    if es_modo_edicion
                    else "Carga varias gestiones a la vez y asocia documentos comunes"
                )
                ui.label(descripcion).classes(
                    "text-caption text-gray-600"
                )

        ui.separator().classes("my-2")

        # Contenido principal
        with ui.column().classes("w-full gap-4 p-4"):
            # Sección 1: Tabla de gestiones
            with ui.card().classes("w-full"):
                with ui.row().classes(
                    "w-full items-center justify-between mb-2"
                ):
                    label_texto = (
                        "📋 Gestiones a Editar"
                        if es_modo_edicion
                        else "📋 Gestiones a Crear"
                    )
                    ui.label(label_texto).classes(
                        "text-h6 font-bold"
                    )
                    if not es_modo_edicion:
                        ui.button(
                            "Agregar Fila",
                            icon="add",
                            on_click=lambda: agregar_gestion(),
                        ).props("color=primary outline")

                tabla_container = ui.column().classes("w-full")

            ui.separator().classes("my-4")

            # Sección 2: Documentos compartidos
            with ui.card().classes("w-full"):
                ui.label("📎 Documentos Compartidos").classes(
                    "text-h6 font-bold mb-2"
                )
                ui.label(
                    "Estos documentos se asociarán a TODAS las gestiones creadas"
                ).classes("text-caption text-gray-600 mb-2")

                with ui.row().classes(
                    "w-full items-center gap-2 mb-2"
                ):
                    ui.upload(
                        label="Subir Documento",
                        auto_upload=True,
                        on_upload=lambda e: subir_documento(e),
                        multiple=True,
                    ).props("color=primary").classes("flex-grow")

                documentos_container = ui.column().classes(
                    "w-full"
                )

            ui.separator().classes("my-4")

            # Opciones de guardado (solo en modo creación)
            generar_pagos_check = None
            if not es_modo_edicion:
                with ui.card().classes("w-full"):
                    ui.label("⚙️ Opciones de Guardado").classes(
                        "text-h6 font-bold mb-2"
                    )
                    generar_pagos_check = ui.checkbox(
                        "Generar pagos automáticamente para cada gestión",
                        value=False,
                    ).classes("mb-2")
                    ui.label(
                        "Si se marca, se creará un pago por TRANSFERENCIA de SOS a PRESTADOR por el total de factura de cada gestión"
                    ).classes("text-caption text-gray-600")

                ui.separator().classes("my-4")

            # Botones de acción
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button(
                    "Cancelar",
                    icon="close",
                    on_click=dialog.close,
                ).props("outline")

                boton_texto = (
                    "Actualizar Todas"
                    if es_modo_edicion
                    else "Guardar Todas"
                )
                ui.button(
                    boton_texto,
                    icon="save",
                    on_click=lambda: guardar_todas_gestiones(
                        generar_pagos=(
                            generar_pagos_check.value
                            if generar_pagos_check
                            else False
                        )
                    ),
                ).props("color=primary")

    def agregar_gestion(data: dict = None):
        """Agrega una nueva fila a la tabla de gestiones"""
        nueva_gestion = data or {
            "fecha": date.today().isoformat(),
            "cliente": "",
            "dominio": "",
            "poliza": "",
            "tipo": None,
            "motivo": "",
            "ncaso": 0,
            "usuariocarga": "",
            "usuariorespuesta": "",
            "estado": None,
            "itr": 0,
            "totalfactura": 0.0,
            "terminado": 0,
            "obs": "",
            "activa": 1,
        }
        gestiones_data.append(nueva_gestion)
        actualizar_tabla_gestiones()

    def eliminar_gestion(index: int):
        """Elimina una gestión de la lista"""
        if 0 <= index < len(gestiones_data):
            gestiones_data.pop(index)
            actualizar_tabla_gestiones()

    def actualizar_tabla_gestiones():
        """Actualiza la tabla de gestiones"""
        tabla_container.clear()

        with tabla_container:
            if not gestiones_data:
                ui.label(
                    "No hay gestiones agregadas. Haz clic en 'Agregar Fila' para comenzar."
                ).classes("text-gray-500 text-center p-4")
                return

            # Crear una card por cada gestión para mejor edición
            for idx, gestion in enumerate(gestiones_data):
                with ui.card().classes("w-full p-3 mb-2"):
                    with ui.row().classes(
                        "w-full items-start gap-2"
                    ):
                        # Número de gestión
                        with ui.column().classes("gap-1"):
                            label_text = f"Gestión #{idx + 1}"
                            if es_modo_edicion and gestion.get(
                                "id"
                            ):
                                label_text += (
                                    f" (ID: {gestion['id']})"
                                )
                            ui.label(label_text).classes(
                                "text-subtitle2 font-bold"
                            )

                            if not es_modo_edicion:
                                ui.button(
                                    icon="delete",
                                    on_click=lambda i=idx: eliminar_gestion(
                                        i
                                    ),
                                ).props(
                                    "flat dense color=negative size=sm"
                                )

                        # Formulario compacto
                        with ui.grid(columns=4).classes(
                            "flex-grow gap-2"
                        ):
                            ui.date_input(
                                label="Fecha",
                                value=gestion["fecha"],
                                on_change=lambda e,
                                i=idx: actualizar_campo(
                                    i, "fecha", e.value
                                ),
                            ).props("dense").classes("col-span-1")

                            ui.input(
                                label="Cliente",
                                value=gestion["cliente"],
                                on_change=lambda e,
                                i=idx: actualizar_campo(
                                    i, "cliente", e.value
                                ),
                            ).props("dense").classes("col-span-1")

                            dominio_input = (
                                ui.input(
                                    label="Dominio",
                                    value=gestion["dominio"],
                                    on_change=lambda e,
                                    i=idx: actualizar_dominio(
                                        i, e.value
                                    ),
                                )
                                .props("dense")
                                .classes("col-span-1")
                            )

                            # Normalizar el valor al escribir
                            dominio_input.on(
                                "update:model-value",
                                lambda e: e.sender.set_value(
                                    e.args.upper().replace(
                                        " ", ""
                                    )
                                    if e.args
                                    else e.args
                                ),
                            )

                            ui.input(
                                label="Póliza *",
                                value=gestion["poliza"],
                                on_change=lambda e,
                                i=idx: actualizar_campo(
                                    i, "poliza", e.value
                                ),
                            ).props("dense").classes("col-span-1")

                            crear_tipo_select(
                                value=gestion["tipo"],
                                label="Tipo *",
                                dense=True,
                                on_change=lambda e,
                                i=idx: actualizar_campo(
                                    i, "tipo", e.value
                                ),
                            ).classes("col-span-1")

                            ui.input(
                                label="Motivo",
                                value=gestion["motivo"],
                                on_change=lambda e,
                                i=idx: actualizar_campo(
                                    i, "motivo", e.value
                                ),
                            ).props("dense").classes("col-span-1")

                            ui.number(
                                label="Nro. Caso",
                                value=gestion["ncaso"],
                                on_change=lambda e,
                                i=idx: actualizar_campo(
                                    i, "ncaso", e.value or 0
                                ),
                            ).props("dense").classes("col-span-1")

                            crear_estado_select(
                                value=gestion["estado"],
                                label="Estado",
                                dense=True,
                                on_change=lambda e,
                                i=idx: actualizar_campo(
                                    i, "estado", e.value
                                ),
                            ).classes("col-span-1")

                            ui.number(
                                label="Total Factura",
                                value=gestion["totalfactura"],
                                format="%.2f",
                                on_change=lambda e,
                                i=idx: actualizar_campo(
                                    i,
                                    "totalfactura",
                                    e.value or 0.0,
                                ),
                            ).props("dense").classes("col-span-2")

                            ui.textarea(
                                label="Observaciones",
                                value=gestion["obs"],
                                on_change=lambda e,
                                i=idx: actualizar_campo(
                                    i, "obs", e.value
                                ),
                            ).props("dense").classes("col-span-4")

    def actualizar_campo(index: int, campo: str, valor):
        """Actualiza un campo de una gestión"""
        if 0 <= index < len(gestiones_data):
            gestiones_data[index][campo] = valor

    def actualizar_dominio(index: int, valor):
        """Actualiza el dominio normalizándolo (uppercase y sin espacios)"""
        if 0 <= index < len(gestiones_data):
            # Normalizar: uppercase y sin espacios
            valor_normalizado = (
                valor.upper().replace(" ", "") if valor else valor
            )
            gestiones_data[index]["dominio"] = valor_normalizado
            return valor_normalizado

    async def subir_documento(e):
        """Maneja la subida de documentos"""
        if not hasattr(e, "file") or not e.file:
            ui.notify(
                "No se seleccionó ningún archivo", type="warning"
            )
            return

        nombre_archivo = e.file.name
        contenido = await e.file.read()

        if not contenido or not nombre_archivo:
            ui.notify(
                "Error al procesar el archivo", type="warning"
            )
            return

        # Guardar temporalmente
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

            # Definir ruta final
            extension = Path(nombre_archivo).suffix
            archivo_destino = docs_dir / f"{file_hash}{extension}"

            # Mover archivo si no existe
            if not archivo_destino.exists():
                os.rename(tmp_path, str(archivo_destino))
            else:
                os.unlink(tmp_path)

            # Agregar a lista de documentos pendientes
            documentos_pendientes.append(
                {
                    "titulo": nombre_archivo,
                    "nombre_archivo": nombre_archivo,
                    "ruta": str(archivo_destino),
                    "hash": file_hash,
                    "tamano": file_size,
                    "mime_type": mime_type,
                    "descripcion": "",
                }
            )

            actualizar_lista_documentos()
            ui.notify(
                f"Documento '{nombre_archivo}' agregado",
                type="positive",
            )

        except Exception as ex:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            ui.notify(
                f"Error subiendo archivo: {str(ex)}",
                type="negative",
            )

    def eliminar_documento(index: int):
        """Elimina un documento de la lista"""
        if 0 <= index < len(documentos_pendientes):
            doc = documentos_pendientes.pop(index)
            # Eliminar archivo físico si no está en la BD
            try:
                ruta = Path(doc["ruta"])
                if ruta.exists():
                    # Verificar si ya existe en la BD
                    existe = database.cursor.execute(
                        "SELECT id FROM documentos WHERE hash = :hash",
                        {"hash": doc["hash"]},
                    ).fetchone()
                    if not existe:
                        ruta.unlink()
            except Exception as e:
                print(f"Error eliminando archivo: {e}")

            actualizar_lista_documentos()
            ui.notify("Documento eliminado", type="info")

    def actualizar_lista_documentos():
        """Actualiza la lista de documentos"""
        documentos_container.clear()

        with documentos_container:
            if not documentos_pendientes:
                ui.label("No hay documentos agregados").classes(
                    "text-gray-500"
                )
                return

            with ui.column().classes("w-full gap-2"):
                for idx, doc in enumerate(documentos_pendientes):
                    with ui.card().classes("w-full p-2"):
                        with ui.row().classes(
                            "w-full items-center gap-2"
                        ):
                            ui.icon("description").classes(
                                "text-blue-600"
                            )

                            with ui.column().classes("flex-grow"):
                                ui.label(doc["titulo"]).classes(
                                    "font-bold"
                                )
                                ui.label(
                                    f"{doc['nombre_archivo']} - {formatear_tamano(doc['tamano'])}"
                                ).classes(
                                    "text-caption text-gray-600"
                                )

                            ui.button(
                                icon="delete",
                                on_click=lambda i=idx: eliminar_documento(
                                    i
                                ),
                            ).props("flat dense color=negative")

    def guardar_todas_gestiones(generar_pagos=False):
        """Guarda todas las gestiones, asocia los documentos y opcionalmente genera pagos"""
        if not gestiones_data:
            ui.notify(
                "No hay gestiones para crear", type="warning"
            )
            return

        # Validar que todas las gestiones tengan los campos requeridos
        errores = []
        for idx, gestion in enumerate(gestiones_data):
            if not gestion.get("poliza"):
                errores.append(
                    f"Gestión #{idx + 1}: Póliza es obligatoria"
                )
            if not gestion.get("tipo"):
                errores.append(
                    f"Gestión #{idx + 1}: Tipo es obligatorio"
                )
            if generar_pagos and (
                not gestion.get("totalfactura")
                or gestion.get("totalfactura") <= 0
            ):
                errores.append(
                    f"Gestión #{idx + 1}: Total factura debe ser mayor a 0 para generar pagos"
                )

        if errores:
            ui.notify(
                "Errores de validación:\n" + "\n".join(errores),
                type="negative",
            )
            return

        # Mostrar dialog de progreso
        with ui.dialog() as progreso_dialog, ui.card():
            ui.label("Guardando gestiones...").classes("text-h6")
            progreso_label = ui.label("").classes("text-body2")
            ui.spinner(size="lg")

        progreso_dialog.open()

        # Guardar gestiones
        gestiones_creadas = []
        gestiones_info = []  # Para almacenar info de gestiones para pagos
        fallos = []

        for idx, gestion in enumerate(gestiones_data):
            # Detectar si es modo edición (si la gestión tiene ID)
            es_actualizacion = "id" in gestion and gestion["id"]

            if es_actualizacion:
                progreso_label.text = f"Actualizando gestión {idx + 1} de {len(gestiones_data)}..."
            else:
                progreso_label.text = f"Creando gestión {idx + 1} de {len(gestiones_data)}..."

            # Para gestiones masivas, ngestion siempre es 0
            ngestion = 0

            # Normalizar dominio antes de guardar (por si acaso)
            dominio_normalizado = (
                gestion["dominio"].upper().replace(" ", "")
                if gestion.get("dominio")
                else ""
            )

            if es_actualizacion:
                # Actualizar gestión existente
                exito, mensaje = database.actualizar_gestion(
                    gestion_id=gestion["id"],
                    ngestion=ngestion,
                    fecha=gestion["fecha"],
                    cliente=gestion["cliente"],
                    dominio=dominio_normalizado,
                    poliza=gestion["poliza"],
                    tipo=gestion["tipo"],
                    motivo=gestion["motivo"],
                    ncaso=gestion["ncaso"],
                    usuariocarga=gestion["usuariocarga"],
                    usuariorespuesta=gestion["usuariorespuesta"],
                    estado=gestion["estado"],
                    itr=gestion["itr"],
                    totalfactura=gestion["totalfactura"],
                    terminado=gestion["terminado"],
                    obs=gestion["obs"],
                    activa=gestion["activa"],
                )
                gestion_id = gestion["id"]
            else:
                # Crear nueva gestión
                exito, mensaje = database.crear_gestion(
                    ngestion=ngestion,
                    fecha=gestion["fecha"],
                    cliente=gestion["cliente"],
                    dominio=dominio_normalizado,
                    poliza=gestion["poliza"],
                    tipo=gestion["tipo"],
                    motivo=gestion["motivo"],
                    ncaso=gestion["ncaso"],
                    usuariocarga=gestion["usuariocarga"],
                    usuariorespuesta=gestion["usuariorespuesta"],
                    estado=gestion["estado"],
                    itr=gestion["itr"],
                    totalfactura=gestion["totalfactura"],
                    terminado=gestion["terminado"],
                    obs=gestion["obs"],
                    activa=gestion["activa"],
                )
                gestion_id = database.cursor.lastrowid

            if exito:
                gestiones_creadas.append(gestion_id)
                gestiones_info.append(
                    {
                        "id": gestion_id,
                        "fecha": gestion["fecha"],
                        "totalfactura": gestion["totalfactura"],
                    }
                )
            else:
                fallos.append(f"Gestión #{idx + 1}: {mensaje}")

        # Generar pagos si se solicitó
        pagos_creados = 0
        fallos_pagos = []
        if generar_pagos and gestiones_info:
            progreso_label.text = "Generando pagos..."

            # Usar valores específicos: SOS -> PRESTADOR por TRANSFERENCIA
            pagador = "SOS"
            destinatario = "PRESTADOR"
            formapago = "TRANSFERENCIA"

            # Verificar que existan en la BD
            pagador_id = database.obtener_agente_id_por_nombre(
                pagador
            )
            destinatario_id = (
                database.obtener_agente_id_por_nombre(
                    destinatario
                )
            )
            formapago_id = (
                database.obtener_formapago_id_por_nombre(
                    formapago
                )
            )

            if not pagador_id:
                fallos_pagos.append(
                    f"No existe el agente '{pagador}' en la base de datos"
                )
            if not destinatario_id:
                fallos_pagos.append(
                    f"No existe el agente '{destinatario}' en la base de datos"
                )
            if not formapago_id:
                fallos_pagos.append(
                    f"No existe la forma de pago '{formapago}' en la base de datos"
                )

            if pagador_id and destinatario_id and formapago_id:
                # Crear pagos para cada gestión
                for gestion_info in gestiones_info:
                    exito, mensaje = database.crear_pago(
                        gestion_id=gestion_info["id"],
                        fecha=gestion_info["fecha"],
                        pagador=pagador,
                        destinatario=destinatario,
                        formapago=formapago,
                        importe=gestion_info["totalfactura"],
                    )

                    if exito:
                        pagos_creados += 1
                    else:
                        fallos_pagos.append(
                            f"Pago para gestión {gestion_info['id']}: {mensaje}"
                        )

        # Asociar documentos a todas las gestiones creadas
        if documentos_pendientes and gestiones_creadas:
            progreso_label.text = "Asociando documentos..."

            for doc in documentos_pendientes:
                # Verificar si el documento ya existe en la BD
                existe = database.cursor.execute(
                    "SELECT id FROM documentos WHERE hash = :hash",
                    {"hash": doc["hash"]},
                ).fetchone()

                if existe:
                    documento_id = existe["id"]
                else:
                    # Crear el documento
                    database.cursor.execute(
                        """INSERT INTO documentos 
                           (titulo, descripcion, nombre_archivo, mime_type, tamano, hash, ruta, creado_por)
                           VALUES (:titulo, :descripcion, :nombre_archivo, :mime_type, :tamano, :hash, :ruta, :creado_por)""",
                        {
                            "titulo": doc["titulo"],
                            "descripcion": doc.get(
                                "descripcion", ""
                            ),
                            "nombre_archivo": doc[
                                "nombre_archivo"
                            ],
                            "mime_type": doc["mime_type"],
                            "tamano": doc["tamano"],
                            "hash": doc["hash"],
                            "ruta": doc["ruta"],
                            "creado_por": None,
                        },
                    )
                    documento_id = database.cursor.lastrowid

                # Asociar a todas las gestiones creadas
                for gestion_id in gestiones_creadas:
                    try:
                        database.cursor.execute(
                            """INSERT INTO gestion_documento (gestion_id, documento_id)
                               VALUES (:gestion_id, :documento_id)""",
                            {
                                "gestion_id": gestion_id,
                                "documento_id": documento_id,
                            },
                        )
                    except Exception as e:
                        print(
                            f"Error asociando documento a gestión {gestion_id}: {e}"
                        )

            database.conn.commit()

        progreso_dialog.close()

        # Mostrar resultado
        accion = "actualizadas" if es_modo_edicion else "creadas"
        mensaje_final = f"✓ {len(gestiones_creadas)} gestiones {accion} exitosamente"
        if pagos_creados > 0:
            mensaje_final += (
                f"\n✓ {pagos_creados} pagos generados"
            )
        if documentos_pendientes:
            mensaje_final += f"\n✓ {len(documentos_pendientes)} documentos asociados"
        if fallos:
            mensaje_final += (
                "\n✗ "
                + str(len(fallos))
                + " errores:\n"
                + "\n".join(fallos)
            )
        if fallos_pagos:
            mensaje_final += (
                "\n✗ Errores en pagos:\n"
                + "\n".join(fallos_pagos)
            )

        ui.notify(
            mensaje_final,
            type="positive"
            if not fallos and not fallos_pagos
            else "warning",
        )

        # Cerrar dialog y refrescar
        dialog.close()
        if refresh_callback:
            refresh_callback()

    # Inicializar tabla
    if es_modo_edicion:
        # En modo edición, mostrar las gestiones cargadas
        actualizar_tabla_gestiones()
    else:
        # En modo creación, inicializar con una fila vacía
        agregar_gestion()

    return dialog
