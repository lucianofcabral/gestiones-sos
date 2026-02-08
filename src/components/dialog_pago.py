"""Dialog para mostrar y editar detalles de un pago"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from nicegui import ui
from src.db.connection import get_database

if TYPE_CHECKING:
    from src.db.database import SQLiteDB


def crear_dialog_pago(pago_id: int, refresh_callback=None):
    """
    Crea un dialog para mostrar y editar un pago.

    Siguiendo las mejores prácticas de NiceGUI:
    - Consulta datos frescos de la BD
    - Retorna el dialog para que el llamador lo controle
    - Recibe callback para refrescar la vista padre

    Args:
        pago_id: ID del pago a mostrar/editar
        refresh_callback: Función a llamar cuando se actualice/elimine el pago

    Returns:
        ui.dialog: El dialog creado (sin abrir)
    """
    database = get_database()

    # Obtener datos frescos de la BD
    pago = database.obtener_pago_por_id(pago_id)

    if not pago:
        ui.notify("Pago no encontrado", type="negative")
        return None

    with (
        ui.dialog() as dialog,
        ui.card().classes("w-full max-w-2xl"),
    ):
        # Encabezado con información principal
        _crear_encabezado(pago)

        ui.separator().classes("my-2")

        # Formulario de edición
        with ui.column().classes("w-full gap-4 p-4"):
            # Crear inputs del formulario
            inputs = _crear_formulario(database, pago)

            ui.separator().classes("mt-4")

            # Botones de acción
            _crear_botones_accion(
                dialog=dialog,
                database=database,
                pago=pago,
                inputs=inputs,
                refresh_callback=refresh_callback,
            )

    return dialog


def _crear_encabezado(pago: dict):
    """Crea el encabezado del dialog con información del pago"""
    with ui.row().classes(
        "w-full items-center bg-purple-100 dark:bg-purple-900/30 p-4 rounded-lg"
    ):
        # Icono principal
        ui.icon("payments", size="3rem").classes(
            "text-purple-600"
        )

        with ui.column().classes("flex-1 gap-1 ml-4"):
            # Título principal
            ui.label("Detalle de Pago").classes(
                "text-h5 font-bold"
            )

            # Info en badges
            with ui.row().classes("gap-2 items-center"):
                with ui.badge().props("outline color=primary"):
                    ui.icon("assignment").classes("mr-1")
                    ui.label(f"Gestión #{pago['ngestion']}")

                with ui.badge().props("outline color=secondary"):
                    ui.icon("description").classes("mr-1")
                    ui.label(f"Póliza {pago['poliza']}")

                with ui.badge().props("outline color=accent"):
                    ui.icon("directions_car").classes("mr-1")
                    ui.label(f"{pago['dominio']}")

            # Cliente
            if pago.get("cliente"):
                with ui.row().classes("items-center gap-1 mt-1"):
                    ui.icon("person", size="sm").classes(
                        "text-gray-500"
                    )
                    ui.label(pago["cliente"]).classes(
                        "text-sm text-gray-600"
                    )


def _crear_formulario(database: SQLiteDB, pago: dict) -> dict:
    """
    Crea el formulario de edición del pago.

    Returns:
        dict: Diccionario con referencias a los inputs creados y label de pasada
    """
    inputs = {}

    # Indicador de nota de crédito (si aplica)
    fp: str = pago.get("formapago", "")
    es_nota_no_pasada = pago.get("es_nota_credito_no_pasada") == 1

    if fp == "Nota De Credito" and es_nota_no_pasada:
        with ui.card().classes(
            "w-full bg-red-50 border-l-4 border-red-500 p-3"
        ):
            with ui.row().classes("items-center gap-2"):
                ui.icon("warning", size="lg").classes(
                    "text-red-600"
                )
                with ui.column().classes("gap-0"):
                    ui.label(
                        "⚠️ Nota de Crédito NO Pasada"
                    ).classes("text-h6 font-bold text-red-700")
                    ui.label(
                        "Esta nota de crédito aún no ha sido procesada en SOS"
                    ).classes("text-sm text-red-600")

    with ui.grid(columns=2).classes("w-full gap-4"):
        # Columna 1: Fecha e Importe
        with ui.column().classes("gap-3"):
            ui.label("📅 Información Financiera").classes(
                "text-subtitle1 font-bold"
            )

            inputs["fecha"] = ui.date_input(
                label="Fecha del Pago",
                value=pago.get("fecha", date.today()),
            ).props("format=YYYY-MM-DD filled")

            inputs["importe"] = ui.number(
                label="Importe",
                value=pago.get("importe", 0),
                prefix="$ ",
                min=1,
                format="%.2f",
            ).props("filled")

        # Columna 2: Forma de pago
        with ui.column().classes("gap-3"):
            ui.label("💳 Método de Pago").classes(
                "text-subtitle1 font-bold"
            )

            inputs["formapago"] = ui.select(
                options=database.obtener_formaspago(),
                value=fp,
                label="Forma de Pago",
            ).props("filled")
            inputs["pasada_label"] = None  # Ya no se usa inline

    # Fila completa para agentes
    ui.label("👥 Participantes").classes(
        "text-subtitle1 font-bold mt-3"
    )

    with ui.grid(columns=2).classes("w-full gap-4 mt-2"):
        inputs["pagador"] = ui.select(
            options=database.obtener_agentes(),
            value=pago.get("pagador", ""),
            label="Pagador",
        ).props("filled")

        inputs["destinatario"] = ui.select(
            options=database.obtener_agentes(),
            value=pago.get("destinatario", ""),
            label="Destinatario",
        ).props("filled")

    return inputs


def _crear_botones_accion(
    dialog: ui.dialog,
    database: SQLiteDB,
    pago: dict,
    inputs: dict,
    refresh_callback,
):
    """Crea los botones de acción (Guardar, Eliminar, Cerrar)"""

    def guardar_cambios():
        """Guarda los cambios del pago en la base de datos"""
        try:
            # Validar fecha
            if inputs["fecha"].value == "":
                ui.notify(
                    "La fecha no puede estar vacía",
                    type="warning",
                )
                return
            fecha_str = str(inputs["fecha"].value)

            # Validar pagador
            if inputs["pagador"].value == "":
                ui.notify(
                    "El pagador no puede estar vacío",
                    type="warning",
                )
                return
            pagador_val = inputs["pagador"].value

            # Validar destinatario
            if inputs["destinatario"].value == "":
                ui.notify(
                    "El destinatario no puede estar vacío",
                    type="warning",
                )
                return
            destinatario_val = inputs["destinatario"].value

            # Validar forma de pago
            if inputs["formapago"].value == "":
                ui.notify(
                    "La forma de pago no puede estar vacía",
                    type="warning",
                )
                return

            # Verificar si es nota de crédito no pasada
            if (
                inputs["formapago"].value == "Nota De Credito"
                and pago.get("es_nota_credito_no_pasada") == 1
            ):
                ui.notify(
                    "No se puede editar una 'Nota De Crédito' que NO ha sido pasada a SOS.",
                    type="warning",
                )
                return

            formapago_val = inputs["formapago"].value
            importe_val = (
                float(inputs["importe"].value)
                if inputs["importe"].value
                else None
            )

            # Actualizar en la base de datos
            resultado = database.actualizar_pago(
                pago_id=pago["id"],
                fecha=fecha_str,
                pagador=pagador_val,
                destinatario=destinatario_val,
                formapago=formapago_val,
                importe=importe_val,
            )

            if resultado:
                ui.notify(
                    "Pago actualizado correctamente",
                    type="positive",
                )
                dialog.close()
                if refresh_callback:
                    refresh_callback()
            else:
                ui.notify(
                    "Error al actualizar el pago", type="negative"
                )
        except Exception as e:
            ui.notify(f"Error: {str(e)}", type="negative")
            print(f"Error al guardar pago: {e}")

    def eliminar_pago():
        """Elimina el pago con confirmación"""
        # Verificar si es nota de crédito pasada
        fp: str = pago.get("formapago", "")
        if (
            fp == "Nota De Credito"
            and pago.get("es_nota_credito_no_pasada") == 0
        ):
            with (
                ui.dialog() as error_dialog,
                ui.card().classes("p-6"),
            ):
                with ui.column().classes("items-center gap-3"):
                    ui.icon("error", size="3rem").classes(
                        "text-red-500"
                    )
                    ui.label("No se puede eliminar").classes(
                        "text-h6 font-bold"
                    )
                    ui.label(
                        "Esta Nota de Crédito ya fue pasada a SOS y no puede eliminarse."
                    ).classes("text-center")
                    ui.button(
                        "Entendido",
                        on_click=error_dialog.close,
                    ).props("color=primary")
            error_dialog.open()
            return

        with (
            ui.dialog() as confirm_dialog,
            ui.card().classes("p-6"),
        ):
            with ui.column().classes("items-center gap-4"):
                ui.icon("warning", size="3rem").classes(
                    "text-orange-500"
                )

                ui.label("¿Eliminar este pago?").classes(
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
                            resultado = database.eliminar_pago(
                                pago["id"]
                            )
                            if resultado:
                                ui.notify(
                                    "Pago eliminado correctamente",
                                    type="positive",
                                )
                                confirm_dialog.close()
                                dialog.close()
                                if refresh_callback:
                                    refresh_callback()
                            else:
                                ui.notify(
                                    "Error al eliminar el pago",
                                    type="negative",
                                )
                        except Exception as e:
                            ui.notify(
                                f"Error: {str(e)}",
                                type="negative",
                            )
                            print(f"Error al eliminar pago: {e}")

                    ui.button(
                        "Eliminar",
                        icon="delete",
                        on_click=confirmar_eliminacion,
                    ).props("color=negative")

        confirm_dialog.open()

    # Botones
    with ui.row().classes("w-full justify-between gap-3 mt-2"):
        # Botón destructivo a la izquierda
        ui.button(
            "Eliminar",
            icon="delete",
            on_click=eliminar_pago,
        ).props("color=negative outline")

        # Botones de acción a la derecha
        with ui.row().classes("gap-2"):
            ui.button("Cancelar", on_click=dialog.close).props(
                "flat"
            )
            ui.button(
                "Guardar Cambios",
                icon="save",
                on_click=guardar_cambios,
            ).props("color=primary")
