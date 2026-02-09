"""Página de gestión de períodos (facturas)"""

from nicegui import ui
from src.db.connection import get_database
from src.components.navbar import crear_navbar
import datetime


def tabla_notas_sin_factura(refresh_callback=None):
    """Tabla de notas de crédito sin factura asociada"""
    database = get_database()
    notas: list[dict] = database.obtener_notas_sin_factura()

    # Mensaje si no hay notas
    if not notas:
        with ui.card().classes("w-full p-8 text-center"):
            ui.icon("check_circle", size="2rem").classes(
                "text-green-400"
            )
            ui.label(
                "No hay notas de crédito sin asignar"
            ).classes("text-body1 text-gray-500")
        return None

    columns = [
        {
            "name": "id",
            "label": "ID",
            "field": "id",
            "align": "left",
            "sortable": True,
            "classes": "hidden",
            "headerClasses": "hidden",
        },
        {
            "name": "ngestion",
            "label": "Nro. Gestión",
            "field": "ngestion",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "dominio",
            "label": "Dominio",
            "field": "dominio",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "poliza",
            "label": "Póliza",
            "field": "poliza",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "cliente",
            "label": "Cliente",
            "field": "cliente",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "fecha",
            "label": "Fecha",
            "field": "fecha",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "importe",
            "label": "Importe",
            "field": "importe",
            "align": "right",
            "sortable": True,
            ":format": "val => val != null ? '$ ' + val.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '-'",
        },
    ]

    rows = [n for n in notas]

    table = (
        ui.table(
            columns=columns,
            rows=rows,
            row_key="id",
            selection="multiple",
            pagination={"rowsPerPage": 10},
            title="Notas de Crédito sin Factura Asociada",
        )
        .classes("w-full")
        .props('color="deep-purple"')
    )

    # Función para asignar notas seleccionadas a una factura
    def asignar_notas():
        if not table.selected or len(table.selected) == 0:
            ui.notify(
                "Selecciona al menos una nota", type="warning"
            )
            return

        nota_ids = [nota["id"] for nota in table.selected]
        total_importe = sum(
            nota["importe"] for nota in table.selected
        )

        # Dialog para elegir entre factura nueva o existente
        with ui.dialog() as dialog, ui.card().classes("w-auto"):
            ui.label(
                f"Asignar {len(nota_ids)} nota(s) seleccionada(s)"
            ).classes("text-h6")
            ui.label(
                f"Importe total: ${total_importe:,.2f}"
            ).classes("text-subtitle2 text-gray-500")

            ui.separator().classes("my-4")

            # Opción: Factura Nueva
            with (
                ui.card()
                .classes("w-full p-4 cursor-pointer")
                .on(
                    "click",
                    lambda: (
                        dialog.close(),
                        crear_factura_nueva_con_notas(
                            nota_ids, total_importe
                        ),
                    ),
                )
            ):
                with ui.row().classes("items-center gap-3"):
                    ui.icon("add_circle", size="2rem").classes(
                        "text-green-500"
                    )
                    with ui.column():
                        ui.label("Crear Nueva Factura").classes(
                            "text-h6"
                        )
                        ui.label(
                            "Se creará un nuevo período con estas notas"
                        ).classes("text-caption text-gray-500")

            ui.separator().classes("my-2")

            # Opción: Factura Existente
            with (
                ui.card()
                .classes("w-full p-4 cursor-pointer")
                .on(
                    "click",
                    lambda: (
                        dialog.close(),
                        asignar_a_factura_existente(nota_ids),
                    ),
                )
            ):
                with ui.row().classes("items-center gap-3"):
                    ui.icon("assignment", size="2rem").classes(
                        "text-blue-500"
                    )
                    with ui.column():
                        ui.label(
                            "Asignar a Factura Existente"
                        ).classes("text-h6")
                        ui.label(
                            "Elige un período existente"
                        ).classes("text-caption text-gray-500")

            ui.separator().classes("my-4")

            with ui.row().classes("w-full justify-end"):
                ui.button(
                    "Cancelar", on_click=dialog.close
                ).props("flat")

        dialog.open()

    def crear_factura_nueva_con_notas(nota_ids, total_importe):
        """Crea una nueva factura con las notas seleccionadas"""
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("📄 Nueva Factura con Notas").classes(
                "text-h6"
            )

            periodo_input = ui.number(
                "Período", value=None, format="%.0f"
            ).classes("w-full")

            fecha_hoy = datetime.date.today().isoformat()
            fecha_input = ui.input(
                "Fecha Emitida", value=fecha_hoy
            ).classes("w-full")
            fecha_input.props("type=date")

            importe_input = (
                ui.number(
                    "Importe Factura",
                    value=total_importe,
                    format="%.2f",
                    step=0.01,
                )
                .classes("w-full")
                .props("prefix=$")
            )

            ui.label(
                f"Se asignarán {len(nota_ids)} nota(s) a esta factura"
            ).classes("text-caption text-deep-purple-500 mt-2")

            with ui.row().classes(
                "w-full justify-end gap-2 mt-4"
            ):
                ui.button(
                    "Cancelar", on_click=dialog.close
                ).props("flat")

                def guardar():
                    if not periodo_input.value:
                        ui.notify(
                            "El período es obligatorio",
                            type="warning",
                        )
                        return

                    if not fecha_input.value:
                        ui.notify(
                            "La fecha es obligatoria",
                            type="warning",
                        )
                        return

                    exito, mensaje = (
                        database.crear_factura_con_notas(
                            int(periodo_input.value),
                            fecha_input.value,
                            float(importe_input.value),
                            nota_ids,
                        )
                    )

                    if exito:
                        ui.notify(mensaje, type="positive")
                        dialog.close()
                        if refresh_callback:
                            refresh_callback()
                    else:
                        ui.notify(mensaje, type="negative")

                ui.button(
                    "Crear y Asignar",
                    icon="add",
                    on_click=guardar,
                ).props("color=primary")

        dialog.open()

    def asignar_a_factura_existente(nota_ids):
        """Asigna las notas a una factura existente"""
        facturas = database.obtener_facturas()

        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("📋 Seleccionar Período Existente").classes(
                "text-h6"
            )

            if not facturas:
                ui.label(
                    "No hay facturas disponibles. Crea una nueva."
                ).classes("text-body2 text-gray-500")
                ui.button(
                    "Cerrar", on_click=dialog.close
                ).classes("mt-4")
            else:
                factura_options = {
                    f[
                        "id"
                    ]: f"Período {f['periodo']} - ${f['importefactura']:,.2f}"
                    for f in facturas
                }

                factura_select = ui.select(
                    label="Período",
                    options=factura_options,
                    value=None,
                ).classes("w-full")

                ui.label(
                    f"Se asignarán {len(nota_ids)} nota(s)"
                ).classes(
                    "text-caption text-deep-purple-500 mt-2"
                )

                with ui.row().classes(
                    "w-full justify-end gap-2 mt-4"
                ):
                    ui.button(
                        "Cancelar", on_click=dialog.close
                    ).props("flat")

                    def asignar():
                        if not factura_select.value:
                            ui.notify(
                                "Selecciona un período",
                                type="warning",
                            )
                            return

                        exito, mensaje = (
                            database.asignar_notas_a_factura(
                                nota_ids, factura_select.value
                            )
                        )

                        if exito:
                            ui.notify(mensaje, type="positive")
                            dialog.close()
                            if refresh_callback:
                                refresh_callback()
                        else:
                            ui.notify(mensaje, type="negative")

                    ui.button(
                        "Asignar",
                        icon="assignment",
                        on_click=asignar,
                    ).props("color=primary")

        dialog.open()

    return table, asignar_notas


def tabla_periodos(refresh_callback=None):
    """Tabla de períodos/facturas"""
    database = get_database()
    facturas: list[dict] = database.obtener_facturas()

    # Mensaje si no hay facturas
    if not facturas:
        with ui.card().classes("w-full p-8 text-center"):
            ui.icon("search_off", size="4rem").classes(
                "text-gray-400"
            )
            ui.label("No se encontraron períodos").classes(
                "text-h6 text-gray-500"
            )
        return

    columns = [
        {
            "name": "id",
            "label": "ID",
            "field": "id",
            "align": "left",
            "sortable": True,
            "classes": "hidden",
            "headerClasses": "hidden",
        },
        {
            "name": "periodo",
            "label": "Período",
            "field": "periodo",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "importefactura",
            "label": "Importe Factura",
            "field": "importefactura",
            "align": "right",
            "sortable": True,
            ":format": "val => val != null ? '$ ' + val.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '-'",
        },
        {
            "name": "cantnotas",
            "label": "Cant. Notas",
            "field": "cantnotas",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "importenotas",
            "label": "Importe Notas",
            "field": "importenotas",
            "align": "right",
            "sortable": True,
            ":format": "val => val != null ? '$ ' + val.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '-'",
        },
    ]

    rows = [f for f in facturas]

    table = ui.table(
        columns=columns,
        rows=rows,
        row_key="id",
        selection="single",
        pagination={"rowsPerPage": 15},
        title="Períodos (Facturas)",
    ).classes("w-full")

    # Función para mostrar el detalle/edición de la factura
    def mostrar_detalle_factura():
        """Muestra un dialog con los detalles de la factura seleccionada"""
        if not table.selected or len(table.selected) == 0:
            return

        factura = table.selected[0]
        factura_id = factura["id"]

        # Obtener datos actualizados de la factura
        factura_data = database.obtener_factura_por_id(factura_id)
        notas_asociadas = database.obtener_notas_de_factura(
            factura_id
        )

        # Crear dialog para editar
        with (
            ui.dialog() as dialog,
            ui.card().classes("w-auto min-w-96 max-w-4xl"),
        ):
            ui.label("📄 Editar Período (Factura)").classes(
                "text-h6 mb-4"
            )

            # Dividir en dos columnas
            with ui.row().classes("w-full gap-4"):
                # Columna izquierda: Campos de edición
                with ui.column().classes("w-96"):
                    # Campos de edición
                    periodo_input = ui.number(
                        "Período",
                        value=factura_data.get("periodo", 0),
                        format="%.0f",
                    ).classes("w-full")

                    fecha_input = ui.input(
                        "Fecha Emitida",
                        value=factura_data.get(
                            "fechaemitida", ""
                        ),
                    ).classes("w-full")
                    fecha_input.props("type=date")

                    importe_input = (
                        ui.number(
                            "Importe",
                            value=factura_data.get(
                                "importe", 0.0
                            ),
                            format="%.2f",
                            step=0.01,
                        )
                        .classes("w-full")
                        .props("prefix=$")
                    )

                # Columna derecha: Tabla de notas asociadas
                with ui.column().classes("flex-1"):
                    ui.label("🔗 Notas Asociadas").classes(
                        "text-subtitle1 mb-2"
                    )

                    if not notas_asociadas:
                        with ui.card().classes(
                            "w-full p-4 text-center"
                        ):
                            ui.label(
                                "No hay notas asociadas"
                            ).classes(
                                "text-caption text-gray-500"
                            )
                    else:
                        columns_notas = [
                            {
                                "name": "id",
                                "label": "ID",
                                "field": "id",
                                "align": "left",
                                "classes": "hidden",
                                "headerClasses": "hidden",
                            },
                            {
                                "name": "ngestion",
                                "label": "N° Gest.",
                                "field": "ngestion",
                                "align": "center",
                                "sortable": True,
                            },
                            {
                                "name": "dominio",
                                "label": "Dominio",
                                "field": "dominio",
                                "align": "center",
                                "sortable": True,
                            },
                            {
                                "name": "cliente",
                                "label": "Cliente",
                                "field": "cliente",
                                "align": "left",
                                "sortable": True,
                            },
                            {
                                "name": "importe",
                                "label": "Importe",
                                "field": "importe",
                                "align": "right",
                                "sortable": True,
                                ":format": "val => val != null ? '$ ' + val.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '-'",
                            },
                        ]

                        tabla_notas = ui.table(
                            columns=columns_notas,
                            rows=notas_asociadas,
                            row_key="id",
                            selection="single",
                            pagination={"rowsPerPage": 5},
                        ).classes("w-full")

                        def desasociar_nota_seleccionada():
                            """Desasocia la nota seleccionada"""
                            if (
                                not tabla_notas.selected
                                or len(tabla_notas.selected) == 0
                            ):
                                return

                            nota = tabla_notas.selected[0]
                            nota_id = nota["id"]

                            # Dialog de confirmación
                            with (
                                ui.dialog() as confirm_dialog,
                                ui.card(),
                            ):
                                ui.label(
                                    f"¿Desasociar nota de gestión {nota['ngestion']}?"
                                ).classes("text-h6")
                                ui.label(
                                    "La nota quedará sin factura asignada."
                                ).classes(
                                    "text-caption text-gray-500 mt-2"
                                )

                                with ui.row().classes(
                                    "w-full justify-end gap-2 mt-4"
                                ):
                                    ui.button(
                                        "Cancelar",
                                        on_click=confirm_dialog.close,
                                    ).props("flat")

                                    def confirmar_desasociacion():
                                        exito, mensaje = (
                                            database.desasociar_nota_de_factura(
                                                nota_id
                                            )
                                        )
                                        if exito:
                                            ui.notify(
                                                mensaje,
                                                type="positive",
                                            )
                                            confirm_dialog.close()
                                            dialog.close()
                                            if refresh_callback:
                                                refresh_callback()
                                        else:
                                            ui.notify(
                                                mensaje,
                                                type="negative",
                                            )

                                    ui.button(
                                        "Desasociar",
                                        on_click=confirmar_desasociacion,
                                    ).props("color=warning")

                            confirm_dialog.open()

                        tabla_notas.on(
                            "selection",
                            lambda: desasociar_nota_seleccionada(),
                        )

            ui.separator().classes("my-4")

            # Botones de acción
            with ui.row().classes("w-full justify-between"):
                # Botón Eliminar (izquierda)
                ui.button(
                    "Eliminar Período",
                    icon="delete",
                    on_click=lambda: eliminar_factura(
                        factura_id, dialog
                    ),
                ).props("color=negative")

                ui.space()

                # Botones Cancelar y Guardar (derecha)
                with ui.row().classes("gap-2"):
                    ui.button(
                        "Cancelar",
                        on_click=dialog.close,
                    ).props("flat")

                    ui.button(
                        "Guardar Cambios",
                        icon="save",
                        on_click=lambda: guardar_factura(
                            factura_id,
                            periodo_input.value,
                            fecha_input.value,
                            importe_input.value,
                            dialog,
                        ),
                    ).props("color=primary")

        dialog.open()

    def guardar_factura(
        factura_id, periodo, fecha, importe, dialog
    ):
        """Guarda los cambios de la factura"""
        if not periodo:
            ui.notify("El período es obligatorio", type="warning")
            return

        if not fecha:
            ui.notify("La fecha es obligatoria", type="warning")
            return

        exito, mensaje = database.actualizar_factura(
            factura_id, int(periodo), fecha, float(importe)
        )

        if exito:
            ui.notify(mensaje, type="positive")
            dialog.close()
            if refresh_callback:
                refresh_callback()
        else:
            ui.notify(mensaje, type="negative")

    def eliminar_factura(factura_id, dialog):
        """Elimina la factura"""
        with ui.dialog() as confirm_dialog, ui.card():
            ui.label(
                "¿Está seguro que desea eliminar este período?"
            )
            with ui.row().classes(
                "w-full justify-end gap-2 mt-4"
            ):
                ui.button(
                    "Cancelar", on_click=confirm_dialog.close
                ).props("flat")

                def confirmar_eliminacion():
                    exito, mensaje = database.eliminar_factura(
                        factura_id
                    )
                    if exito:
                        ui.notify(mensaje, type="positive")
                        confirm_dialog.close()
                        dialog.close()
                        if refresh_callback:
                            refresh_callback()
                    else:
                        ui.notify(mensaje, type="negative")

                ui.button(
                    "Eliminar", on_click=confirmar_eliminacion
                ).props("color=negative")

        confirm_dialog.open()

    # EVENTO DE SELECCIÓN
    table.on("selection", lambda: mostrar_detalle_factura())


@ui.page("/periodos")
def page_periodos():
    """Página de períodos (facturas)"""
    # Aplicar decorador ui.refreshable en scope local
    tabla_periodos_refreshable = ui.refreshable(tabla_periodos)

    def refresh_tabla():
        """Callback para refrescar la tabla"""
        tabla_periodos_refreshable.refresh()

    def crear_nueva_factura():
        """Abre dialog para crear nueva factura"""
        database = get_database()

        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("📄 Nuevo Período (Factura)").classes(
                "text-h6"
            )

            # Campos de creación
            periodo_input = ui.number(
                "Período",
                value=None,
                format="%.0f",
            ).classes("w-full")

            # Fecha por defecto: hoy
            fecha_hoy = datetime.date.today().isoformat()
            fecha_input = ui.input(
                "Fecha Emitida",
                value=fecha_hoy,
            ).classes("w-full")
            fecha_input.props("type=date")

            importe_input = (
                ui.number(
                    "Importe",
                    value=0.0,
                    format="%.2f",
                    step=0.01,
                )
                .classes("w-full")
                .props("prefix=$")
            )

            # Botones de acción
            with ui.row().classes(
                "w-full justify-end gap-2 mt-4"
            ):
                ui.button(
                    "Cancelar",
                    on_click=dialog.close,
                ).props("flat")

                def guardar_nueva():
                    if not periodo_input.value:
                        ui.notify(
                            "El período es obligatorio",
                            type="warning",
                        )
                        return

                    if not fecha_input.value:
                        ui.notify(
                            "La fecha es obligatoria",
                            type="warning",
                        )
                        return

                    exito, mensaje = database.crear_factura(
                        int(periodo_input.value),
                        fecha_input.value,
                        float(importe_input.value),
                    )

                    if exito:
                        ui.notify(mensaje, type="positive")
                        dialog.close()
                        refresh_tabla()
                    else:
                        ui.notify(mensaje, type="negative")

                ui.button(
                    "Crear",
                    icon="add",
                    on_click=guardar_nueva,
                ).props("color=primary")

        dialog.open()

    # Configurar colores del tema - Paleta Períodos (Índigo/Teal/Ámbar)
    ui.colors(
        primary="#5e35b1", secondary="#00897b", accent="#ffa000"
    )
    dark = ui.dark_mode(value=True)
    crear_navbar(dark)

    with ui.column().classes(
        "w-full max-w-7xl mx-auto p-4 gap-4"
    ):
        # ====================
        # ENCABEZADO
        # ====================
        with ui.row().classes(
            "w-full items-center justify-between"
        ):
            ui.label("📅 Gestión de Períodos (Facturas)").classes(
                "text-h4"
            )

            ui.button(
                "Nuevo Período",
                icon="add",
                on_click=crear_nueva_factura,
            ).props("color=primary")

        # ====================
        # NOTAS SIN FACTURA
        # ====================
        with ui.row().classes(
            "w-full items-center justify-between mt-4"
        ):
            ui.label("⚠️ Notas de Crédito sin Factura").classes(
                "text-h5"
            )

        # Crear tabla de notas con funcionalidad refreshable
        tabla_notas_refreshable = ui.refreshable(
            tabla_notas_sin_factura
        )

        def refresh_todo():
            """Refresca ambas tablas"""
            refresh_tabla()
            tabla_notas_refreshable.refresh()

        result = tabla_notas_refreshable(
            refresh_callback=refresh_todo
        )

        # Si hay notas, mostrar el botón de asignar
        if result and len(result) == 2:
            table_notas, asignar_notas_fn = result
            with ui.row().classes("w-full justify-end mt-2"):
                ui.button(
                    "Asignar Notas Seleccionadas",
                    icon="assignment_turned_in",
                    on_click=asignar_notas_fn,
                ).props("color=secondary")

        # ====================
        # SEPARADOR
        # ====================
        ui.separator().classes("my-6")

        # ====================
        # TABLA PERÍODOS
        # ====================
        tabla_periodos_refreshable(refresh_callback=refresh_tabla)

    with ui.footer().classes("bg-transparent"):
        ui.label(
            "💡 Tip: Haz clic en una fila para editar o eliminar"
        ).classes("text-center w-full text-gray-500")
