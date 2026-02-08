"""Dialog para mostrar, editar y crear gestiones"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from nicegui import ui
from src.db.connection import get_database
from src.components.dialog_pago import crear_dialog_pago

if TYPE_CHECKING:
    from src.db.database import SQLiteDB


def crear_dialog_gestion(
    gestion_id: int | None = None, refresh_callback=None
):
    """
    Crea un dialog para crear o editar una gestión.

    Args:
        gestion_id: ID de la gestión a editar (None para crear nueva)
        refresh_callback: Función a llamar cuando se actualice/cree la gestión

    Returns:
        ui.dialog: El dialog creado (sin abrir)
    """
    database = get_database()

    # Si hay ID, obtener datos de la gestión
    gestion = None
    if gestion_id is not None:
        gestion = database.obtener_gestion_por_id(gestion_id)
        if not gestion:
            ui.notify("Gestión no encontrada", type="negative")
            return None

    es_nuevo = gestion_id is None

    with (
        ui.dialog() as dialog,
        ui.card().classes(
            "w-full max-w-4xl max-h-[90vh] overflow-auto"
        ),
    ):
        # Encabezado
        _crear_encabezado(gestion, es_nuevo)

        ui.separator().classes("my-2")

        # Formulario
        with ui.column().classes("w-full gap-4 p-4"):
            inputs = _crear_formulario(
                database, gestion, es_nuevo
            )

            # Tabla de pagos (solo si no es nueva)
            if not es_nuevo:
                ui.separator().classes("mt-4")
                _crear_tabla_pagos(gestion["id"], database)

            ui.separator().classes("mt-4")

            # Botones de acción
            _crear_botones_accion(
                dialog=dialog,
                database=database,
                gestion=gestion,
                inputs=inputs,
                refresh_callback=refresh_callback,
                es_nuevo=es_nuevo,
            )

    return dialog


def _crear_encabezado(gestion: dict | None, es_nuevo: bool):
    """Crea el encabezado del dialog"""
    with ui.row().classes(
        "w-full items-center bg-blue-100 dark:bg-blue-900/30 p-4 rounded-lg"
    ):
        # Icono principal
        icono = "add_circle" if es_nuevo else "edit"
        ui.icon(icono, size="3rem").classes("text-blue-600")

        with ui.column().classes("flex-1 gap-1 ml-4"):
            # Título principal
            titulo = (
                "Nueva Gestión" if es_nuevo else "Editar Gestión"
            )
            ui.label(titulo).classes("text-h5 font-bold")

            # Info de la gestión existente
            if not es_nuevo and gestion:
                with ui.row().classes("gap-2 items-center"):
                    with ui.badge().props(
                        "outline color=primary"
                    ):
                        ui.icon("assignment").classes("mr-1")
                        ui.label(
                            f"Nro. {gestion.get('ngestion', 0)}"
                        )

                    with ui.badge().props(
                        "outline color=secondary"
                    ):
                        ui.icon("description").classes("mr-1")
                        ui.label(
                            f"Póliza {gestion.get('poliza', '')}"
                        )

                    with ui.badge().props("outline color=accent"):
                        ui.icon("directions_car").classes("mr-1")
                        ui.label(f"{gestion.get('dominio', '')}")

                    # Estado Terminado
                    terminado = gestion.get("terminado", 0)
                    if terminado:
                        with ui.badge().props("color=green"):
                            ui.icon("check_circle").classes(
                                "mr-1"
                            )
                            ui.label("Terminado")
                    else:
                        with ui.badge().props("color=orange"):
                            ui.icon("pending").classes("mr-1")
                            ui.label("Pendiente")


def _crear_formulario(
    database: SQLiteDB, gestion: dict | None, es_nuevo: bool
) -> dict:
    """Crea el formulario de edición/creación"""
    inputs = {}

    # Valores por defecto para nueva gestión
    valores = (
        gestion
        if gestion
        else {
            "ngestion": 0,
            "fecha": date.today(),
            "cliente": "",
            "dominio": "",
            "poliza": "",
            "tipo": "",
            "motivo": "",
            "ncaso": 0,
            "usuariocarga": "",
            "usuariorespuesta": "",
            "estado": 0,
            "itr": 0,
            "totalfactura": 0.0,
            "terminado": 0,
            "obs": "",
            "activa": 1,
        }
    )

    # Primera fila: Información básica
    with ui.card().classes("w-full"):
        ui.label("📋 Información Básica").classes(
            "text-h6 font-bold mb-3"
        )

        with ui.grid(columns=3).classes("w-full gap-4"):
            inputs["ngestion"] = ui.number(
                label="Nro. Gestión",
                value=valores.get("ngestion", 0),
                min=0,
            ).props("filled readonly")

            inputs["fecha"] = ui.date_input(
                label="Fecha",
                value=valores.get("fecha", date.today()),
            ).props("format=YYYY-MM-DD filled")

            inputs["tipo"] = ui.select(
                options=database.obtener_tipos()
                or ["Especial", "Normal", "Urgente"],
                value=valores.get("tipo", ""),
                label="Tipo",
                with_input=True,
            ).props("filled")

    # Segunda fila: Datos del vehículo y póliza
    with ui.card().classes("w-full mt-3"):
        ui.label("🚗 Vehículo y Póliza").classes(
            "text-h6 font-bold mb-3"
        )

        with ui.grid(columns=3).classes("w-full gap-4"):
            inputs["dominio"] = ui.input(
                label="Dominio",
                value=valores.get("dominio", ""),
            ).props("filled")

            inputs["poliza"] = ui.input(
                label="Nro. Póliza",
                value=valores.get("poliza", ""),
            ).props("filled")

            inputs["cliente"] = ui.input(
                label="Cliente",
                value=valores.get("cliente", ""),
            ).props("filled")

    # Tercera fila: Detalles
    with ui.card().classes("w-full mt-3"):
        ui.label("📝 Detalles").classes("text-h6 font-bold mb-3")

        with ui.grid(columns=2).classes("w-full gap-4"):
            inputs["motivo"] = ui.input(
                label="Motivo",
                value=valores.get("motivo", ""),
            ).props("filled readonly")

            inputs["totalfactura"] = ui.number(
                label="Total Factura",
                value=valores.get("totalfactura", 0.0),
                prefix="$ ",
                format="%.2f",
                min=0,
            ).props("filled")

        inputs["obs"] = (
            ui.textarea(
                label="Observaciones",
                value=valores.get("obs", ""),
            )
            .props("filled")
            .classes("w-full")
        )

    # Cuarta fila: Control y estado
    with ui.card().classes("w-full mt-3"):
        ui.label("⚙️ Estado y Control").classes(
            "text-h6 font-bold mb-3"
        )

        with ui.grid(columns=3).classes("w-full gap-4"):
            inputs["ncaso"] = ui.number(
                label="Nro. Caso",
                value=valores.get("ncaso", 0),
                min=0,
            ).props("filled readonly")

            inputs["itr"] = ui.number(
                label="ITR",
                value=valores.get("itr", 0),
                min=0,
            ).props("filled readonly")

            inputs["estado"] = ui.number(
                label="Estado",
                value=valores.get("estado", 0),
                min=0,
            ).props("filled readonly")

        with ui.grid(columns=2).classes("w-full gap-4 mt-3"):
            inputs["usuariocarga"] = ui.input(
                label="Usuario Carga",
                value=valores.get("usuariocarga", ""),
            ).props("filled readonly")

            inputs["usuariorespuesta"] = ui.input(
                label="Usuario Respuesta",
                value=valores.get("usuariorespuesta", ""),
            ).props("filled readonly")

    return inputs


def _crear_tabla_pagos(gestion_id: int, database: SQLiteDB):
    """Crea la tabla de pagos relacionados con la gestión"""
    with ui.card().classes("w-full mt-3"):
        with ui.row().classes("items-center mb-3 w-full"):
            ui.icon("payments", size="2rem").classes(
                "text-purple-600"
            )
            ui.label("💳 Pagos Relacionados").classes(
                "text-h6 font-bold ml-2 flex-1"
            )

            # Botón para refrescar pagos
            def refrescar_tabla():
                """Refresca los datos de la tabla de pagos"""
                pagos_data = database.obtener_pagos_por_gestion(
                    gestion_id
                )
                # Formatear el importe
                for pago in pagos_data:
                    if "importe" in pago:
                        pago["importe_formateado"] = (
                            f"$ {pago['importe']:,.2f}"
                        )
                tabla_pagos.rows = pagos_data
                ui.notify("Tabla actualizada", type="positive")

            ui.button(
                icon="refresh",
                on_click=refrescar_tabla,
            ).props("flat round")

        # Obtener pagos de esta gestión
        pagos_data = database.obtener_pagos_por_gestion(
            gestion_id
        )

        # Formatear el importe antes de pasarlo a la tabla
        for pago in pagos_data:
            if "importe" in pago:
                pago["importe_formateado"] = (
                    f"$ {pago['importe']:,.2f}"
                )

        # Definir columnas
        columnas_pagos = [
            {
                "name": "fecha",
                "label": "Fecha",
                "field": "fecha",
                "sortable": True,
                "align": "left",
            },
            {
                "name": "pagador",
                "label": "Pagador",
                "field": "pagador",
                "sortable": True,
                "align": "left",
            },
            {
                "name": "destinatario",
                "label": "Destinatario",
                "field": "destinatario",
                "sortable": True,
                "align": "left",
            },
            {
                "name": "formapago",
                "label": "Forma de Pago",
                "field": "formapago",
                "sortable": True,
                "align": "left",
            },
            {
                "name": "importe_formateado",
                "label": "Importe",
                "field": "importe_formateado",
                "sortable": True,
                "align": "right",
            },
        ]

        # Crear tabla
        tabla_pagos = ui.table(
            columns=columnas_pagos,
            rows=pagos_data,
            row_key="id",
            pagination={"rowsPerPage": 5},
        ).classes("w-full")

        # Agregar slot para hacer las filas clickeables
        tabla_pagos.add_slot(
            "body",
            r"""
            <q-tr :props="props" @click="$parent.$emit('row_click', props.row)" class="cursor-pointer hover:bg-blue-50">
                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                    {{ col.value }}
                </q-td>
            </q-tr>
        """,
        )

        def abrir_dialog_pago(e):
            """Abre el dialog de pago al hacer clic en una fila"""
            pago_id = e.args.get("id")
            if pago_id:
                dialog_pago = crear_dialog_pago(
                    pago_id, refrescar_tabla
                )
                if dialog_pago:
                    dialog_pago.open()

        tabla_pagos.on("row_click", abrir_dialog_pago)

        if not pagos_data:
            ui.label(
                "No hay pagos registrados para esta gestión"
            ).classes(
                "text-grey-6 italic text-center w-full py-4"
            )


def _crear_botones_accion(
    dialog: ui.dialog,
    database: SQLiteDB,
    gestion: dict | None,
    inputs: dict,
    refresh_callback,
    es_nuevo: bool,
):
    """Crea los botones de acción"""

    def guardar_cambios():
        """Guarda los cambios o crea nueva gestión"""
        try:
            # Validar campos requeridos
            if not inputs["poliza"].value:
                ui.notify(
                    "La póliza es obligatoria", type="warning"
                )
                return

            if not inputs["tipo"].value:
                ui.notify(
                    "El tipo es obligatorio", type="warning"
                )
                return

            if not inputs["fecha"].value:
                ui.notify(
                    "La fecha es obligatoria", type="warning"
                )
                return

            # Preparar datos
            datos = {
                "ngestion": int(inputs["ngestion"].value or 0),
                "fecha": str(inputs["fecha"].value),
                "cliente": inputs["cliente"].value or "",
                "dominio": inputs["dominio"].value or "",
                "poliza": inputs["poliza"].value,
                "tipo": inputs["tipo"].value,
                "motivo": inputs["motivo"].value or "",
                "ncaso": int(inputs["ncaso"].value or 0),
                "usuariocarga": inputs["usuariocarga"].value
                or "",
                "usuariorespuesta": inputs[
                    "usuariorespuesta"
                ].value
                or "",
                "estado": int(inputs["estado"].value or 0),
                "itr": int(inputs["itr"].value or 0),
                "totalfactura": float(
                    inputs["totalfactura"].value or 0
                ),
                "obs": inputs["obs"].value or "",
            }

            # Mantener valores existentes de campos no editables
            if not es_nuevo and gestion:
                datos["terminado"] = gestion.get("terminado", 0)

                datos["activa"] = gestion.get("activa", 1)
            else:
                # Valores por defecto para nueva gestión
                datos["terminado"] = 0
                datos["activa"] = 1

            if es_nuevo:
                # Crear nueva gestión
                resultado, mensaje = database.crear_gestion(
                    **datos
                )
            else:
                # Actualizar gestión existente
                resultado, mensaje = database.actualizar_gestion(
                    gestion_id=gestion["id"], **datos
                )

            if resultado:
                ui.notify(mensaje, type="positive")
                dialog.close()
                if refresh_callback:
                    refresh_callback()
            else:
                ui.notify(mensaje, type="negative")

        except Exception as e:
            ui.notify(f"Error: {str(e)}", type="negative")
            print(f"Error al guardar gestión: {e}")

    def eliminar_gestion():
        """Elimina la gestión con confirmación"""
        if es_nuevo:
            return  # No se puede eliminar algo que no existe

        with (
            ui.dialog() as confirm_dialog,
            ui.card().classes("p-6"),
        ):
            with ui.column().classes("items-center gap-4"):
                ui.icon("warning", size="3rem").classes(
                    "text-orange-500"
                )
                ui.label("¿Eliminar esta gestión?").classes(
                    "text-h6 font-bold"
                )
                ui.label(
                    "Esta acción no se puede deshacer."
                ).classes("text-center text-gray-600")

                with ui.row().classes(
                    "w-full justify-center gap-3 mt-2"
                ):
                    ui.button(
                        "Cancelar",
                        on_click=confirm_dialog.close,
                    ).props("outline")

                    def confirmar_eliminacion():
                        try:
                            resultado = database.eliminar_gestion(
                                gestion["id"]
                            )
                            if resultado:
                                ui.notify(
                                    "Gestión eliminada correctamente",
                                    type="positive",
                                )
                                confirm_dialog.close()
                                dialog.close()
                                if refresh_callback:
                                    refresh_callback()
                            else:
                                ui.notify(
                                    "Error al eliminar la gestión",
                                    type="negative",
                                )
                        except Exception as e:
                            ui.notify(
                                f"Error: {str(e)}",
                                type="negative",
                            )
                            print(
                                f"Error al eliminar gestión: {e}"
                            )

                    ui.button(
                        "Eliminar",
                        icon="delete",
                        on_click=confirmar_eliminacion,
                    ).props("color=negative")

        confirm_dialog.open()

    # Botones
    with ui.row().classes("w-full justify-between gap-3 mt-2"):
        # Botón eliminar (solo si no es nuevo)
        if not es_nuevo:
            ui.button(
                "Eliminar",
                icon="delete",
                on_click=eliminar_gestion,
            ).props("color=negative outline")
        else:
            ui.space()

        # Botones de acción a la derecha
        with ui.row().classes("gap-2"):
            ui.button("Cancelar", on_click=dialog.close).props(
                "flat"
            )

            texto_boton = (
                "Crear Gestión" if es_nuevo else "Guardar Cambios"
            )
            ui.button(
                texto_boton,
                icon="save",
                on_click=guardar_cambios,
            ).props("color=primary")
