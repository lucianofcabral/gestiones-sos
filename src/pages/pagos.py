"""Página de gestión de pagos"""

from nicegui import ui
from src.db.database import SQLiteDB
from src.state import filtros_pagos
from src.components.navbar import crear_navbar


def tabla_pagos():
    """Tabla de gestiones con selección"""
    database = SQLiteDB()
    pagos: list[dict[str, any]] = database.filtrar_pagos(
        texto_busqueda=filtros_pagos.texto_busqueda,
        pagador=filtros_pagos.pagador,
        destinatario=filtros_pagos.destinatario,
        formapago=filtros_pagos.formapago,
        es_nota_credito_no_pasada=filtros_pagos.es_nota_credito_no_pasada,
    )

    # Tabla
    if not pagos:
        with ui.card().classes("w-full p-8 text-center"):
            ui.icon("search_off", size="4rem").classes(
                "text-gray-400"
            )
            ui.label("No se encontraron pagos").classes(
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
            "name": "pagador",
            "label": "Pagador",
            "field": "pagador",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "destinatario",
            "label": "Destinatario",
            "field": "destinatario",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "formapago",
            "label": "Forma de Pago",
            "field": "formapago",
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
        {
            "name": "tipo",
            "label": "Tipo",
            "field": "tipo",
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
            "sortable": True,
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
            "name": "es_nota_credito_no_pasada",
            "label": "NO Pasada",
            "field": "es_nota_credito_no_pasada",
            "align": "left",
            "sortable": True,
            ":style": "val => val == 1 ? 'background-color: #f00; color: #991b1b;' : ''",
        },
    ]

    rows = [p for p in pagos]

    table = (
        ui.table(
            columns=columns,
            rows=rows,
            row_key="id",
            selection="single",
            pagination={"rowsPerPage": 12},
            title="Pagos",
        )
        .classes("w-full")
        .props(
            ":row-style=\"row => (row.activa == 0 || row.activa == '0' || row.activa == false) ? 'background-color: #fee !important; color: #991b1b !important;' : ''\""
        )
    )

    # Color condicional para columna activa
    table.add_slot(
        "body-cell-es_nota_credito_no_pasada",
        """
    <q-td :props="props">
        <q-badge :color="props.row.es_nota_credito_no_pasada == 1 || props.row.es_nota_credito_no_pasada == '1' || props.row.es_nota_credito_no_pasada == true ? 'red' : 'green'">
            {{ props.row.es_nota_credito_no_pasada == 1 || props.row.es_nota_credito_no_pasada == '1' || props.row.es_nota_credito_no_pasada == true ? 'SI' : '' }}
        </q-badge>
    </q-td>
    """,
    )


@ui.page("/pagos")
def page_pagos():
    """Página de pagos"""
    # Aplicar decorador ui.refreshable en scope local
    tabla_pagos_refreshable = ui.refreshable(tabla_pagos)

    def aplicar_filtros():
        """Aplica los filtros y actualiza la tabla"""
        tabla_pagos_refreshable.refresh()

    def limpiar_filtros():
        """Limpia todos los filtros"""
        filtros_pagos.texto_busqueda = ""
        filtros_pagos.pagador = "all"
        filtros_pagos.destinatario = "all"
        filtros_pagos.formapago = "all"
        filtros_pagos.es_nota_credito_no_pasada = False

        # Actualizar UI
        pagador_select.value = "all"
        destinatario_select.value = "all"
        formapago_select.value = "all"
        busqueda_input.value = ""

        tabla_pagos_refreshable.refresh()
        ui.notify("Filtros limpiados", type="info")

    def exportar_seleccionados():
        """Exporta pagos seleccionados"""
        if not filtros_pagos.pagos_seleccionados:
            ui.notify(
                "No hay pagos seleccionados", type="warning"
            )
            return

        ui.notify(
            f"Exportando {len(filtros_pagos.pagos_seleccionados)} pagos...",
            type="positive",
        )

    ui.colors(
        primary="#dc2656", secondary="#ea580c", accent="#fbbf24"
    )
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
            with ui.row().classes("w-full gap-4"):
                ui.label("🔍 Filtros").classes("text-h6 q-mb-md")
                ui.space()

                # Pagadores
                with ui.column().classes("w-48"):
                    global pagador_select
                    database = SQLiteDB()
                    pagadores = [
                        "all"
                    ] + database.obtener_agentes()
                    pagador_select = ui.select(
                        options=pagadores,
                        value="all",
                        label="Pagador",
                    ).classes("w-full")

                    def on_pagador_change(e):
                        filtros_pagos.pagador = e.sender.value
                        aplicar_filtros()

                    pagador_select.on(
                        "update:model-value", on_pagador_change
                    )

                # Destinatarios
                with ui.column().classes("w-48"):
                    global destinatario_select
                    destinatarios = [
                        "all"
                    ] + database.obtener_agentes()
                    destinatario_select = ui.select(
                        options=destinatarios,
                        value="all",
                        label="Destinatario",
                    ).classes("w-full")

                    def on_destinatario_change(e):
                        filtros_pagos.destinatario = (
                            e.sender.value
                        )
                        aplicar_filtros()

                    destinatario_select.on(
                        "update:model-value",
                        on_destinatario_change,
                    )

                # Formas de pago
                with ui.column().classes("w-48"):
                    global formapago_select
                    formaspago = [
                        "all"
                    ] + database.obtener_formaspago()
                    formapago_select = ui.select(
                        options=formaspago,
                        value="all",
                        label="Forma de Pago",
                    ).classes("w-full")

                    def on_formapago_change(e):
                        filtros_pagos.formapago = e.sender.value
                        aplicar_filtros()

                    formapago_select.on(
                        "update:model-value", on_formapago_change
                    )

                ui.space()

            # Segunda fila de filtros
            with ui.row().classes("w-full gap-4 items-end"):
                ui.space()

                # Búsqueda por texto
                with ui.column().classes("w-120"):
                    global busqueda_input
                    busqueda_input = (
                        ui.input(
                            "Búsqueda",
                            placeholder="Buscar por nombre o proveedor...",
                        )
                        .classes("w-full")
                        .on_value_change(
                            lambda e: setattr(
                                filtros_pagos,
                                "texcto_busqueda",
                                e.value,
                            )
                            or aplicar_filtros()
                        )
                    )

                global es_nota_credito_no_pasada_check
                es_nota_credito_no_pasada_check = ui.checkbox(
                    "Es Nota de Crédito NO pasada", value=False
                ).on_value_change(
                    lambda e: setattr(
                        filtros_pagos,
                        "es_nota_credito_no_pasada",
                        e.value,
                    )
                    or aplicar_filtros()
                )

                ui.button(
                    "Pasar Notas de crédito a SOS",
                    on_click=exportar_seleccionados,
                    icon="arrow_circle_right",
                ).props("color=secondary")

                ui.button(
                    "Exportar Selección",
                    on_click=exportar_seleccionados,
                    icon="download",
                ).props("color=primary")

                ui.space()

        # ====================
        # TABLA
        # ====================
        tabla_pagos_refreshable()

    with ui.footer().classes("bg-transparent"):
        ui.label(
            "💡 Tip: Los filtros se aplican automáticamente al cambiar"
        ).classes("text-center w-full text-gray-500")
