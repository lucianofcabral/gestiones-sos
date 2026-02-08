"""Página principal de Gestiones"""

from nicegui import ui
from src.db.connection import get_database
from src.state import filtros_gestiones
from src.components.navbar import crear_navbar


def tabla_gestiones():
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
            "name": "motivo",
            "label": "Motivo",
            "field": "motivo",
            "align": "left",
            "sortable": True,
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
            "sortable": True,
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

    # Actualizar selección
    def open_gestion(): ...

    table.on("selection", lambda: open_gestion())


@ui.page("/")
def page_gestiones():
    """Página principal de gestiones"""
    # Aplicar decorador ui.refreshable en scope local
    tabla_gestiones_refreshable = ui.refreshable(tabla_gestiones)

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
            with ui.row().classes("w-full gap-4"):
                ui.label("🔍 Filtros").classes(
                    "text-h6 q-mb-md w-70"
                )

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
        tabla_gestiones_refreshable()

    with ui.footer().classes("bg-transparent"):
        ui.label(
            "💡 Tip: Los filtros se aplican automáticamente al cambiar"
        ).classes("text-center w-full text-gray-500")
