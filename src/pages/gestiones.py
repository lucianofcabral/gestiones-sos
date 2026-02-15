"""Página principal de Gestiones"""

from nicegui import ui
from src.db.connection import get_database
from src.state import filtros_gestiones
from src.components.navbar import crear_navbar
from src.components.dialog_gestion import crear_dialog_gestion
from src.components.dialog_gestiones_masivas import (
    crear_dialog_gestiones_masivas,
)


def tabla_gestiones(refresh_callback=None):
    """Tabla de gestiones con selección"""
    db = get_database()
    gestiones: list[dict[str, any]] = db.filter_gestiones(
        texto_busqueda=filtros_gestiones.texto_busqueda,
        tipo=filtros_gestiones.tipo,
        terminado=filtros_gestiones.terminado,
        no_terminado=filtros_gestiones.no_terminado,
        activa=filtros_gestiones.activa,
        no_activa=filtros_gestiones.no_activa,
        con_pagos=filtros_gestiones.con_pagos,
        sin_pagos=filtros_gestiones.sin_pagos,
        con_nota=filtros_gestiones.con_nota,
        sin_nota=filtros_gestiones.sin_nota,
        con_nota_pasada=filtros_gestiones.con_nota_pasada,
    )

    # Tabla
    if not gestiones:
        with ui.card().classes("w-full p-8 text-center"):
            ui.icon("search_off", size="4rem").classes(
                "text-gray-400"
            )
            ui.label("No se encontraron gestiones").classes(
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
            "name": "fecha",
            "label": "Fecha",
            "field": "fecha",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "ngestion",
            "label": "Nro. Gestion",
            "field": "ngestion",
            "align": "right",
            "sortable": True,
        },
        {
            "name": "dominio",
            "label": "Dominio",
            "field": "dominio",
            "align": "center",
            "sortable": False,
        },
        {
            "name": "poliza",
            "label": "Nro. Poliza",
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
            "name": "motivo",
            "label": "Motivo",
            "field": "motivo",
            "align": "left",
            "sortable": False,
        },
        {
            "name": "estado",
            "label": "Estado",
            "field": "estado",
            "align": "left",
            "sortable": False,
        },
        {
            "name": "totalfactura",
            "label": "Total Factura",
            "field": "totalfactura",
            "align": "right",
            "sortable": True,
            ":format": "val => val != null ? '$ ' + val.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '-'",
        },
        {
            "name": "terminado",
            "label": "Terminado",
            "field": "terminado",
            "align": "center",
            "sortable": True,
            ":style": "val => val == '0' ? 'background-color: #f00; color: #991b1b;' : ''",
        },
        {
            "name": "obs",
            "label": "Observaciones",
            "field": "obs",
            "align": "left",
            "sortable": False,
        },
        {
            "name": "activa",
            "label": "Activa",
            "field": "activa",
            "align": "left",
            "sortable": True,
            ":style": "val => val == 0 ? 'background-color: #f00; color: #991b1b;' : ''",
        },
    ]

    table = (
        ui.table(
            columns=columns,
            rows=gestiones,
            row_key="id",
            selection="single",
            pagination={"rowsPerPage": 8},
            title="Gestiones",
        )
        .classes("w-full")
        .props(
            ":row-style=\"row => (row.activa == 0 || row.activa == '0' || row.activa == false) ? 'background-color: #fee !important; color: #991b1b !important;' : ''\""
        )
    )

    # Color condicional para columna activa
    table.add_slot(
        "body-cell-activa",
        """
    <q-td :props="props">
        <q-badge :color="props.row.activa == 0 ? 'red' : 'green'">
            {{ props.row.activa == 0  ? '' : '' }}
        </q-badge>
    </q-td>
    """,
    )

    table.add_slot(
        "body-cell-terminado",
        """
    <q-td :props="props">
        <q-badge :color="props.row.terminado == 0  ? 'red' : 'green'">
            {{ props.row.terminado == 0  ? '' : '' }}
        </q-badge>
    </q-td>
    """,
    )

    # Función para mostrar el detalle de la gestión
    def open_gestion():
        """Abre el dialog de edición de la gestión seleccionada"""
        if not table.selected or len(table.selected) == 0:
            return

        gestion = table.selected[0]
        gestion_id = gestion["id"]

        # Verificar si hay gestiones relacionadas a través de documentos compartidos
        db = get_database()
        gestiones_relacionadas = (
            db.obtener_gestiones_relacionadas_por_documentos(
                gestion_id
            )
        )

        if (
            gestiones_relacionadas
            and len(gestiones_relacionadas) > 0
        ):
            # Hay gestiones relacionadas, preguntar qué hacer
            def abrir_todas():
                """Abre dialog para editar todas las gestiones relacionadas"""
                # Incluir la gestión actual más las relacionadas
                todas_gestiones = [
                    dict(gestion)
                ] + gestiones_relacionadas

                # Abrir dialog en modo edición con todas las gestiones
                from src.components.dialog_gestiones_masivas import (
                    crear_dialog_gestiones_masivas,
                )

                dialog = crear_dialog_gestiones_masivas(
                    refresh_callback=refresh_callback,
                    gestiones_existentes=todas_gestiones,
                )
                if dialog:
                    dialog.open()
                confirmar_dialog.close()

            def abrir_solo_actual():
                """Abre dialog para editar solo la gestión actual"""
                dialog = crear_dialog_gestion(
                    gestion_id=gestion_id,
                    refresh_callback=refresh_callback,
                )
                if dialog:
                    dialog.open()
                confirmar_dialog.close()

            # Mostrar diálogo de confirmación
            confirmar_dialog = ui.dialog()
            with (
                confirmar_dialog,
                ui.card().classes("w-full max-w-md"),
            ):
                ui.label("Gestiones Relacionadas").classes(
                    "text-h6 font-bold mb-4"
                )

                ui.label(
                    f"Esta gestión comparte documentos con {len(gestiones_relacionadas)} "
                    f"otra{'s' if len(gestiones_relacionadas) > 1 else ''}."
                ).classes("mb-4")

                ui.label("¿Qué desea hacer?").classes("mb-2")

                with ui.row().classes(
                    "w-full justify-end gap-2 mt-4"
                ):
                    ui.button(
                        "Editar Solo Esta",
                        on_click=abrir_solo_actual,
                    ).props("outline color=secondary")

                    ui.button(
                        f"Editar Todas ({len(gestiones_relacionadas) + 1})",
                        on_click=abrir_todas,
                    ).props("color=primary")

            confirmar_dialog.open()
        else:
            # No hay gestiones relacionadas, abrir normalmente
            dialog = crear_dialog_gestion(
                gestion_id=gestion_id,
                refresh_callback=refresh_callback,
            )
            if dialog:
                dialog.open()

    table.on("selection", lambda: open_gestion())


async def importar_excel(refresh_callback=None):
    """Maneja la importación de Excel"""
    uploading_dialog = ui.dialog()
    with uploading_dialog, ui.card().classes("w-full max-w-xl"):
        ui.label("Importar Gestiones desde Excel").classes(
            "text-h6"
        )
        ui.separator()

        ui.label(
            "Selecciona un archivo Excel con las columnas: Fecha, N° Gestion, Cliente, Dominio, Póliza, Tipo, Motivo, N° Caso, Usuario Carga, Usuario Respuesta, Estado, ITR"
        ).classes("text-caption text-grey-7 mb-4")

        result_container = ui.column().classes("w-full")

        async def handle_upload(e):
            result_container.clear()
            with result_container:
                ui.spinner(size="lg")
                ui.label("Procesando archivo...").classes(
                    "text-body2"
                )

            temp_path = None
            try:
                # En NiceGUI, e contiene información del archivo
                import tempfile
                import os
                import shutil

                # e.file es un objeto SmallFileUpload que contiene los bytes del archivo
                # Opción 1: Si tiene _data (bytes), escribirlo a un archivo temporal
                if hasattr(e.file, "_data"):
                    temp_fd, temp_path = tempfile.mkstemp(
                        suffix=".xlsx"
                    )
                    os.write(temp_fd, e.file._data)
                    os.close(temp_fd)
                # Opción 2: Buscar una ruta temporal que exista
                else:
                    source_file = None
                    for attr in [
                        "path",
                        "_path",
                        "file",
                        "_file",
                        "tmpfile",
                    ]:
                        if hasattr(e.file, attr):
                            val = getattr(e.file, attr)
                            if isinstance(
                                val, str
                            ) and os.path.exists(val):
                                source_file = val
                                break

                    if not source_file:
                        raise ValueError(
                            f"No se pudo encontrar la ruta del archivo. Atributos: {[a for a in dir(e.file) if not a.startswith('__')]}"
                        )

                    # Copiar a temp_path
                    temp_fd, temp_path = tempfile.mkstemp(
                        suffix=".xlsx"
                    )
                    os.close(temp_fd)
                    shutil.copy2(source_file, temp_path)

                # Importar
                db = get_database()
                success, stats = (
                    db.importar_gestiones_desde_excel(temp_path)
                )

                result_container.clear()
                with result_container:
                    if success:
                        ui.label(
                            "✅ Importación completada"
                        ).classes("text-h6 text-positive")
                        with ui.card().classes(
                            "w-full bg-positive-1"
                        ):
                            ui.label(
                                f"📝 {stats['actualizadas']} gestiones actualizadas"
                            ).classes("text-body1")
                            ui.label(
                                f"➕ {stats['insertadas']} gestiones insertadas"
                            ).classes("text-body1")

                            if stats["errores"]:
                                ui.separator()
                                ui.label(
                                    f"⚠️ {len(stats['errores'])} errores encontrados:"
                                ).classes(
                                    "text-body2 text-warning"
                                )
                                with ui.scroll_area().classes(
                                    "h-32"
                                ):
                                    for error in stats[
                                        "errores"
                                    ][
                                        :10
                                    ]:  # Mostrar solo los primeros 10
                                        ui.label(
                                            f"• {error}"
                                        ).classes("text-caption")

                        ui.notify(
                            "Importación completada",
                            type="positive",
                        )

                        # Refrescar tabla después de cerrar
                        if refresh_callback:
                            refresh_callback()
                    else:
                        ui.label(
                            "❌ Error en la importación"
                        ).classes("text-h6 text-negative")
                        with ui.card().classes(
                            "w-full bg-negative-1"
                        ):
                            for error in stats.get(
                                "errores", ["Error desconocido"]
                            ):
                                ui.label(f"• {error}").classes(
                                    "text-body2"
                                )
                        ui.notify(
                            "Error en importación",
                            type="negative",
                        )

            except Exception as e:
                result_container.clear()
                with result_container:
                    ui.label(
                        "❌ Error al procesar el archivo"
                    ).classes("text-h6 text-negative")
                    ui.label(str(e)).classes(
                        "text-caption text-grey-7"
                    )
                ui.notify(f"Error: {str(e)}", type="negative")
            finally:
                # Limpiar archivo temporal
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

        ui.upload(
            label="Seleccionar archivo Excel",
            on_upload=handle_upload,
            auto_upload=True,
        ).props('accept=".xlsx,.xls"').classes("w-full")

        with ui.row().classes("w-full justify-end mt-4"):
            ui.button(
                "Cerrar", on_click=uploading_dialog.close
            ).props("outline")

    uploading_dialog.open()


@ui.page("/")
def page_gestiones():
    """Página principal de gestiones"""
    # Aplicar decorador ui.refreshable en scope local
    tabla_gestiones_refreshable = ui.refreshable(tabla_gestiones)

    def refresh_tabla():
        """Callback para refrescar la tabla desde dentro de tabla_gestiones"""
        tabla_gestiones_refreshable.refresh()

    def aplicar_filtros():
        """Aplica los filtros y actualiza la tabla"""
        tabla_gestiones_refreshable.refresh()

    def exportar_seleccionados():
        """Exporta gestiones seleccionados"""
        if not filtros_gestiones.gestiones_seleccionados:
            ui.notify(
                "No hay gestiones seleccionados", type="warning"
            )
            return

        ui.notify(
            f"Exportando {len(filtros_gestiones.gestiones_seleccionados)} gestiones...",
            type="positive",
        )

    # Configurar colores del tema - Paleta Gestiones (Azul/Verde)
    ui.colors(
        primary="#1e88e5", secondary="#26a69a", accent="#66bb6a"
    )

    db = get_database()
    dark = ui.dark_mode(value=True)
    crear_navbar(dark)

    with ui.column().classes(
        "w-full max-w-8xl mx-auto p-2 gap-2"
    ):
        # ====================
        # PANEL DE FILTROS
        # ====================
        with ui.card().classes("w-full"):
            # Primera fila de filtros
            with ui.row().classes("w-full gap-4 items-center"):
                ui.label("🔍 Filtros").classes("text-h6 q-mb-md")

                ui.space()

                # Botón para crear nueva gestión
                def crear_nueva_gestion():
                    dialog = crear_dialog_gestion(
                        gestion_id=None,
                        refresh_callback=refresh_tabla,
                    )
                    if dialog:
                        dialog.open()

                ui.button(
                    "Nueva Gestión",
                    icon="add",
                    on_click=crear_nueva_gestion,
                ).props("color=primary")

                # Botón para crear múltiples gestiones
                def crear_multiples_gestiones():
                    dialog = crear_dialog_gestiones_masivas(
                        refresh_callback=refresh_tabla,
                    )
                    if dialog:
                        dialog.open()

                ui.button(
                    "Agregar Múltiples",
                    icon="playlist_add",
                    on_click=crear_multiples_gestiones,
                ).props("color=primary outline")

                # Botón para importar desde Excel
                ui.button(
                    "Importar Excel",
                    icon="upload_file",
                    on_click=lambda: importar_excel(
                        refresh_tabla
                    ),
                ).props("color=secondary outline")

            with ui.row().classes("w-full gap-4 mt-2"):
                # Tipo
                with ui.column().classes("w-48"):
                    global tipo_select
                    tipos = ["all"] + db.obtener_tipos()
                    tipo_select = ui.select(
                        options=tipos, value="all", label="Tipo"
                    ).classes("w-full")

                    def on_tipo_change(e):
                        filtros_gestiones.tipo = e.sender.value
                        aplicar_filtros()

                    tipo_select.on(
                        "update:model-value", on_tipo_change
                    )

                # Búsqueda por texto
                with ui.column().classes("w-120"):
                    global texto_busqueda_input
                    texto_busqueda_input = (
                        ui.input(
                            "Búsqueda",
                            placeholder="Buscar por nombre o proveedor...",
                        )
                        .classes("w-full")
                        .on_value_change(
                            lambda e: setattr(
                                filtros_gestiones,
                                "texto_busqueda",
                                e.value,
                            )
                            or aplicar_filtros()
                        )
                    )

                ui.button(
                    "Exportar Filtrados",
                    on_click=exportar_seleccionados,
                    icon="download",
                ).props("color=primary")

            # Segunda fila de filtros
            with ui.row().classes("w-full gap-4 items-end"):
                global \
                    terminado_check, \
                    no_terminado_check, \
                    no_activa_check, \
                    activa_check, \
                    con_pagos_check, \
                    sin_pagos_check, \
                    con_nota_check, \
                    sin_nota_check, \
                    con_nota_pasada_check

                ui.space()
                with ui.column().classes("w-48"):
                    ui.label("Estado de la gestión").classes(
                        "text-subtitle2"
                    )

                    terminado_check = ui.checkbox(
                        "Terminados", value=False
                    ).on_value_change(
                        lambda e: setattr(
                            filtros_gestiones,
                            "terminado",
                            e.value,
                        )
                        or aplicar_filtros()
                    )

                    no_terminado_check = ui.checkbox(
                        "NO Terminados", value=True
                    ).on_value_change(
                        lambda e: setattr(
                            filtros_gestiones,
                            "no_terminado",
                            e.value,
                        )
                        or aplicar_filtros()
                    )

                with ui.column().classes("w-48"):
                    ui.label("Activas").classes("text-subtitle2")

                    activa_check = ui.checkbox(
                        "Activas", value=True
                    ).on_value_change(
                        lambda e: setattr(
                            filtros_gestiones,
                            "activa",
                            e.value,
                        )
                        or aplicar_filtros()
                    )

                    no_activa_check = ui.checkbox(
                        "NO Activas", value=False
                    ).on_value_change(
                        lambda e: setattr(
                            filtros_gestiones,
                            "no_activa",
                            e.value,
                        )
                        or aplicar_filtros()
                    )

                with ui.column().classes("w-48"):
                    ui.label("Pagos").classes("text-subtitle2")

                    con_pagos_check = ui.checkbox(
                        "Con Pagos", value=False
                    ).on_value_change(
                        lambda e: setattr(
                            filtros_gestiones,
                            "con_pagos",
                            e.value,
                        )
                        or aplicar_filtros()
                    )

                    sin_pagos_check = ui.checkbox(
                        "Sin Pagos", value=False
                    ).on_value_change(
                        lambda e: setattr(
                            filtros_gestiones,
                            "sin_pagos",
                            e.value,
                        )
                        or aplicar_filtros()
                    )

                with ui.column().classes("w-48"):
                    ui.label("Notas de Crédito").classes(
                        "text-subtitle2"
                    )

                    con_nota_check = ui.checkbox(
                        "Con Nota de Crédito", value=False
                    ).on_value_change(
                        lambda e: setattr(
                            filtros_gestiones,
                            "con_nota",
                            e.value,
                        )
                        or aplicar_filtros()
                    )

                    sin_nota_check = ui.checkbox(
                        "Sin Nota de Crédito", value=False
                    ).on_value_change(
                        lambda e: setattr(
                            filtros_gestiones,
                            "sin_nota",
                            e.value,
                        )
                        or aplicar_filtros()
                    )

                    con_nota_pasada_check = ui.checkbox(
                        "Con Nota de Crédito PASADA", value=False
                    ).on_value_change(
                        lambda e: setattr(
                            filtros_gestiones,
                            "con_nota_pasada",
                            e.value,
                        )
                        or aplicar_filtros()
                    )

                ui.space()
        # ====================
        # TABLA
        # ====================
        tabla_gestiones_refreshable(
            refresh_callback=refresh_tabla
        )

    with ui.footer().classes("bg-transparent"):
        ui.label(
            "💡 Tip: Los filtros se aplican automáticamente al cambiar"
        ).classes("text-center w-full text-gray-500")
