"""Página de reportes"""

from nicegui import ui
import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.components.navbar import crear_navbar
from src.db.database import SQLiteDB


def obtener_datos_pagos():
    """Obtiene los datos de pagos agrupados por fecha y forma de pago"""
    db = SQLiteDB()

    query = """
        SELECT
            p.fecha,
            fp.formapago AS forma_pago,
            sum(p.importe) AS importe,
            count(*) AS pagos
        FROM
            pagos p
        LEFT JOIN gestiones g ON
            g.id = p.gestion_id
        LEFT JOIN formaspago fp ON
            fp.id = p.formapago_id
        WHERE
            g.activa = 1
        GROUP BY
            p.fecha,
            fp.formapago;
        """

    # Ejecutar query y obtener resultados
    db.cursor.execute(query)
    rows = db.cursor.fetchall()

    # Convertir a lista de diccionarios
    data = [dict(row) for row in rows]

    # Crear DataFrame de Polars
    df = pl.DataFrame(data)

    # Convertir fecha a tipo datetime y agregar columnas de año y mes
    df = df.with_columns(
        [
            pl.col("fecha").str.to_date().alias("fecha_dt"),
        ]
    ).with_columns(
        [
            pl.col("fecha_dt").dt.year().alias("anio"),
            pl.col("fecha_dt").dt.month().alias("mes"),
        ]
    )

    # Agrupar por año, mes y forma de pago
    df_resumido = (
        df.group_by(["anio", "mes", "forma_pago"])
        .agg(
            [
                pl.col("importe").sum().alias("importe_total"),
                pl.col("pagos").sum().alias("cantidad_pagos"),
            ]
        )
        .sort(["anio", "mes"])
    )

    return df_resumido


def crear_grafico_pagos_por_mes(df: pl.DataFrame):
    """Crea un gráfico de barras con los pagos por mes y forma de pago"""
    # Crear columna de período (Año-Mes)
    df = df.with_columns(
        [
            (
                pl.col("anio").cast(pl.Utf8)
                + "-"
                + pl.col("mes").cast(pl.Utf8).str.zfill(2)
            ).alias("periodo")
        ]
    )

    # Obtener formas de pago únicas
    formas_pago = df["forma_pago"].unique().sort().to_list()

    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=(
            "Importe Total por Mes y Forma de Pago",
            "Cantidad de Pagos por Mes y Forma de Pago",
        ),
        vertical_spacing=0.15,
    )

    # Gráfico 1: Importe por forma de pago
    for forma in formas_pago:
        df_forma = df.filter(pl.col("forma_pago") == forma).sort(
            "periodo"
        )
        fig.add_trace(
            go.Bar(
                x=df_forma["periodo"].to_list(),
                y=df_forma["importe_total"].to_list(),
                name=forma,
                legendgroup=forma,
            ),
            row=1,
            col=1,
        )

    # Gráfico 2: Cantidad de pagos por forma de pago
    for forma in formas_pago:
        df_forma = df.filter(pl.col("forma_pago") == forma).sort(
            "periodo"
        )
        fig.add_trace(
            go.Bar(
                x=df_forma["periodo"].to_list(),
                y=df_forma["cantidad_pagos"].to_list(),
                name=forma,
                legendgroup=forma,
                showlegend=False,
            ),
            row=2,
            col=1,
        )

    # Actualizar layout
    fig.update_layout(
        height=800,
        showlegend=True,
        barmode="group",
        template="plotly_dark",
        title_text="Análisis de Pagos por Período y Forma de Pago",
        title_x=0.5,
        title_font_size=20,
    )

    fig.update_xaxes(title_text="Período (Año-Mes)", row=2, col=1)
    fig.update_yaxes(title_text="Importe ($)", row=1, col=1)
    fig.update_yaxes(title_text="Cantidad de Pagos", row=2, col=1)

    return fig


def obtener_datos_pagos_agentes():
    """Obtiene los datos de pagos agrupados por fecha, pagador y destinatario"""
    db = SQLiteDB()

    query = """
        SELECT
            p.fecha,
            pag.agente AS pagador,
            des.agente AS destinatario,
            sum(p.importe) AS importe,
            count(*) AS pagos
        FROM
            pagos p
        LEFT JOIN gestiones g ON
            g.id = p.gestion_id
        LEFT JOIN agentes pag ON
            pag.id = p.pagador_id 
        LEFT JOIN agentes des ON
            des.id = p.destinatario_id  
        WHERE
            g.activa = 1
        GROUP BY
            p.fecha,
            pag.agente,
            des.agente;
        """

    # Ejecutar query y obtener resultados
    db.cursor.execute(query)
    rows = db.cursor.fetchall()

    # Convertir a lista de diccionarios
    data = [dict(row) for row in rows]

    # Crear DataFrame de Polars
    df = pl.DataFrame(data)

    # Convertir fecha a tipo datetime y agregar columnas de año y mes
    df = df.with_columns(
        [
            pl.col("fecha").str.to_date().alias("fecha_dt"),
        ]
    ).with_columns(
        [
            pl.col("fecha_dt").dt.year().alias("anio"),
            pl.col("fecha_dt").dt.month().alias("mes"),
        ]
    )

    # Agrupar por año, mes, pagador y destinatario
    df_resumido = (
        df.group_by(["anio", "mes", "pagador", "destinatario"])
        .agg(
            [
                pl.col("importe").sum().alias("importe_total"),
                pl.col("pagos").sum().alias("cantidad_pagos"),
            ]
        )
        .sort(["anio", "mes"])
    )

    return df_resumido


def crear_grafico_pagos_agentes(df: pl.DataFrame):
    """Crea gráficos de pagos por pagador y destinatario"""
    # Crear columna de período (Año-Mes)
    df = df.with_columns(
        [
            (
                pl.col("anio").cast(pl.Utf8)
                + "-"
                + pl.col("mes").cast(pl.Utf8).str.zfill(2)
            ).alias("periodo")
        ]
    )

    # Agrupar por período y pagador
    df_pagador = (
        df.group_by(["periodo", "pagador"])
        .agg(
            [
                pl.col("importe_total").sum().alias("importe"),
                pl.col("cantidad_pagos").sum().alias("pagos"),
            ]
        )
        .sort("periodo")
    )

    # Agrupar por período y destinatario
    df_destinatario = (
        df.group_by(["periodo", "destinatario"])
        .agg(
            [
                pl.col("importe_total").sum().alias("importe"),
                pl.col("cantidad_pagos").sum().alias("pagos"),
            ]
        )
        .sort("periodo")
    )

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Importe por Pagador",
            "Importe por Destinatario",
            "Cantidad Pagos por Pagador",
            "Cantidad Pagos por Destinatario",
        ),
        vertical_spacing=0.12,
        horizontal_spacing=0.1,
    )

    # Gráfico 1: Importe por pagador
    pagadores = df_pagador["pagador"].unique().sort().to_list()
    for pagador in pagadores:
        if pagador:  # Evitar valores nulos
            df_pag = df_pagador.filter(
                pl.col("pagador") == pagador
            ).sort("periodo")
            fig.add_trace(
                go.Bar(
                    x=df_pag["periodo"].to_list(),
                    y=df_pag["importe"].to_list(),
                    name=pagador,
                    legendgroup="pagador",
                ),
                row=1,
                col=1,
            )

    # Gráfico 2: Importe por destinatario
    destinatarios = (
        df_destinatario["destinatario"].unique().sort().to_list()
    )
    for destinatario in destinatarios:
        if destinatario:  # Evitar valores nulos
            df_dest = df_destinatario.filter(
                pl.col("destinatario") == destinatario
            ).sort("periodo")
            fig.add_trace(
                go.Bar(
                    x=df_dest["periodo"].to_list(),
                    y=df_dest["importe"].to_list(),
                    name=destinatario,
                    legendgroup="destinatario",
                    showlegend=True,
                ),
                row=1,
                col=2,
            )

    # Gráfico 3: Cantidad por pagador
    for pagador in pagadores:
        if pagador:
            df_pag = df_pagador.filter(
                pl.col("pagador") == pagador
            ).sort("periodo")
            fig.add_trace(
                go.Bar(
                    x=df_pag["periodo"].to_list(),
                    y=df_pag["pagos"].to_list(),
                    name=pagador,
                    legendgroup="pagador",
                    showlegend=False,
                ),
                row=2,
                col=1,
            )

    # Gráfico 4: Cantidad por destinatario
    for destinatario in destinatarios:
        if destinatario:
            df_dest = df_destinatario.filter(
                pl.col("destinatario") == destinatario
            ).sort("periodo")
            fig.add_trace(
                go.Bar(
                    x=df_dest["periodo"].to_list(),
                    y=df_dest["pagos"].to_list(),
                    name=destinatario,
                    legendgroup="destinatario",
                    showlegend=False,
                ),
                row=2,
                col=2,
            )

    # Actualizar layout
    fig.update_layout(
        height=900,
        showlegend=True,
        barmode="stack",
        template="plotly_dark",
        title_text="Análisis de Pagos por Pagador y Destinatario",
        title_x=0.5,
        title_font_size=20,
    )

    fig.update_xaxes(title_text="Período", row=2, col=1)
    fig.update_xaxes(title_text="Período", row=2, col=2)
    fig.update_yaxes(title_text="Importe ($)", row=1, col=1)
    fig.update_yaxes(title_text="Importe ($)", row=1, col=2)
    fig.update_yaxes(title_text="Cantidad", row=2, col=1)
    fig.update_yaxes(title_text="Cantidad", row=2, col=2)

    return fig


def obtener_datos_sm_comparacion():
    """Obtiene datos de SM como pagador y como destinatario para comparación"""
    db = SQLiteDB()

    # Query para SM como pagador
    query_pagador = """
    SELECT
        p.fecha,
        pag.agente AS agente,
        sum(p.importe) AS importe,
        count(*) AS pagos
    FROM
        pagos p
    LEFT JOIN gestiones g ON
        g.id = p.gestion_id
    LEFT JOIN agentes pag ON
        pag.id = p.pagador_id 
    WHERE
        g.activa = 1
        AND pag.agente = 'SM'
    GROUP BY
        p.fecha,
        pag.agente;
    """

    # Query para SM como destinatario (corregido el JOIN)
    query_destinatario = """
    SELECT
        p.fecha,
        des.agente AS agente,
        sum(p.importe) AS importe,
        count(*) AS pagos
    FROM
        pagos p
    LEFT JOIN gestiones g ON
        g.id = p.gestion_id
    LEFT JOIN agentes des ON
        des.id = p.destinatario_id 
    WHERE
        g.activa = 1
        AND des.agente = 'SM'
    GROUP BY
        p.fecha,
        des.agente;
    """

    # Obtener datos como pagador
    db.cursor.execute(query_pagador)
    rows_pagador = db.cursor.fetchall()
    data_pagador = [dict(row) for row in rows_pagador]

    # Obtener datos como destinatario
    db.cursor.execute(query_destinatario)
    rows_destinatario = db.cursor.fetchall()
    data_destinatario = [dict(row) for row in rows_destinatario]

    # Crear DataFrames de Polars
    df_pagador = (
        pl.DataFrame(data_pagador)
        if data_pagador
        else pl.DataFrame()
    )
    df_destinatario = (
        pl.DataFrame(data_destinatario)
        if data_destinatario
        else pl.DataFrame()
    )

    # Procesar DataFrame de pagador
    if len(df_pagador) > 0:
        df_pagador = df_pagador.with_columns(
            [
                pl.col("fecha").str.to_date().alias("fecha_dt"),
            ]
        ).with_columns(
            [
                pl.col("fecha_dt").dt.year().alias("anio"),
                pl.col("fecha_dt").dt.month().alias("mes"),
            ]
        )

        df_pagador = (
            df_pagador.group_by(["anio", "mes"])
            .agg(
                [
                    pl.col("importe")
                    .sum()
                    .alias("importe_total"),
                    pl.col("pagos").sum().alias("cantidad_pagos"),
                ]
            )
            .sort(["anio", "mes"])
            .with_columns([pl.lit("Pagador").alias("tipo")])
        )

    # Procesar DataFrame de destinatario
    if len(df_destinatario) > 0:
        df_destinatario = df_destinatario.with_columns(
            [
                pl.col("fecha").str.to_date().alias("fecha_dt"),
            ]
        ).with_columns(
            [
                pl.col("fecha_dt").dt.year().alias("anio"),
                pl.col("fecha_dt").dt.month().alias("mes"),
            ]
        )

        df_destinatario = (
            df_destinatario.group_by(["anio", "mes"])
            .agg(
                [
                    pl.col("importe")
                    .sum()
                    .alias("importe_total"),
                    pl.col("pagos").sum().alias("cantidad_pagos"),
                ]
            )
            .sort(["anio", "mes"])
            .with_columns([pl.lit("Destinatario").alias("tipo")])
        )

    return df_pagador, df_destinatario


def crear_grafico_comparacion_sm(
    df_pagador: pl.DataFrame, df_destinatario: pl.DataFrame
):
    """Crea gráficos comparativos de SM como pagador vs destinatario"""

    # Crear columna de período para ambos DataFrames
    if len(df_pagador) > 0:
        df_pagador = df_pagador.with_columns(
            [
                (
                    pl.col("anio").cast(pl.Utf8)
                    + "-"
                    + pl.col("mes").cast(pl.Utf8).str.zfill(2)
                ).alias("periodo")
            ]
        )

    if len(df_destinatario) > 0:
        df_destinatario = df_destinatario.with_columns(
            [
                (
                    pl.col("anio").cast(pl.Utf8)
                    + "-"
                    + pl.col("mes").cast(pl.Utf8).str.zfill(2)
                ).alias("periodo")
            ]
        )

    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=(
            "Comparación Importe: SM como Pagador vs Destinatario",
            "Comparación Cantidad Pagos: SM como Pagador vs Destinatario",
        ),
        vertical_spacing=0.15,
    )

    # Gráfico 1: Importe - SM como Pagador
    if len(df_pagador) > 0:
        fig.add_trace(
            go.Bar(
                x=df_pagador["periodo"].to_list(),
                y=df_pagador["importe_total"].to_list(),
                name="SM como Pagador",
                marker_color="#dc2656",
            ),
            row=1,
            col=1,
        )

    # Gráfico 1: Importe - SM como Destinatario
    if len(df_destinatario) > 0:
        fig.add_trace(
            go.Bar(
                x=df_destinatario["periodo"].to_list(),
                y=df_destinatario["importe_total"].to_list(),
                name="SM como Destinatario",
                marker_color="#ea580c",
            ),
            row=1,
            col=1,
        )

    # Gráfico 2: Cantidad - SM como Pagador
    if len(df_pagador) > 0:
        fig.add_trace(
            go.Bar(
                x=df_pagador["periodo"].to_list(),
                y=df_pagador["cantidad_pagos"].to_list(),
                name="SM como Pagador",
                marker_color="#dc2656",
                showlegend=False,
            ),
            row=2,
            col=1,
        )

    # Gráfico 2: Cantidad - SM como Destinatario
    if len(df_destinatario) > 0:
        fig.add_trace(
            go.Bar(
                x=df_destinatario["periodo"].to_list(),
                y=df_destinatario["cantidad_pagos"].to_list(),
                name="SM como Destinatario",
                marker_color="#ea580c",
                showlegend=False,
            ),
            row=2,
            col=1,
        )

    # Actualizar layout
    fig.update_layout(
        height=800,
        showlegend=True,
        barmode="group",
        template="plotly_dark",
        title_text="Análisis Comparativo: SM como Pagador vs Destinatario",
        title_x=0.5,
        title_font_size=20,
    )

    fig.update_xaxes(title_text="Período (Año-Mes)", row=2, col=1)
    fig.update_yaxes(title_text="Importe ($)", row=1, col=1)
    fig.update_yaxes(title_text="Cantidad de Pagos", row=2, col=1)

    return fig


def obtener_estadisticas_generales():
    """Obtiene estadísticas generales de gestiones y pagos"""
    db = SQLiteDB()

    # Contar gestiones activas
    query_gestiones = """
    SELECT COUNT(*) as total
    FROM gestiones
    WHERE activa = 1;
    """

    db.cursor.execute(query_gestiones)
    gestiones_activas = db.cursor.fetchone()["total"]

    # Obtener suma y cantidad de pagos por forma de pago
    query_formas_pago = """
    SELECT
        fp.formapago AS forma_pago,
        sum(p.importe) AS importe_total,
        count(*) AS cantidad_pagos
    FROM
        pagos p
    LEFT JOIN gestiones g ON
        g.id = p.gestion_id
    LEFT JOIN formaspago fp ON
        fp.id = p.formapago_id
    WHERE
        g.activa = 1
    GROUP BY
        fp.formapago;
    """

    db.cursor.execute(query_formas_pago)
    rows = db.cursor.fetchall()
    formas_pago_stats = [dict(row) for row in rows]

    # Calcular totales generales
    total_pagos = sum(
        fp["cantidad_pagos"] for fp in formas_pago_stats
    )
    total_importe = sum(
        fp["importe_total"] for fp in formas_pago_stats
    )

    return {
        "gestiones_activas": gestiones_activas,
        "total_pagos": total_pagos,
        "total_importe": total_importe,
        "formas_pago": formas_pago_stats,
    }


@ui.page("/reportes")
def page_reportes():
    """Página de reportes"""
    ui.colors(
        primary="#dc2656", secondary="#ea580c", accent="#fbbf24"
    )
    dark = ui.dark_mode(value=True)
    crear_navbar(dark)

    with ui.column().classes(
        "w-full max-w-7xl mx-auto p-4 gap-4"
    ):
        ui.label("📊 Reportes y Estadísticas").classes("text-h4")

        # Obtener datos
        try:
            stats = obtener_estadisticas_generales()
            df_pagos = obtener_datos_pagos()
            df_agentes = obtener_datos_pagos_agentes()
            df_sm_pagador, df_sm_destinatario = (
                obtener_datos_sm_comparacion()
            )

            # Tarjetas de estadísticas generales
            with ui.row().classes("w-full gap-4 mb-4"):
                # Tarjeta gestiones activas
                with ui.card().classes("flex-1 p-4"):
                    with ui.row().classes("items-center gap-3"):
                        ui.icon(
                            "folder_open", size="2.5rem"
                        ).classes("text-primary")
                        with ui.column().classes("gap-0"):
                            ui.label("Gestiones Activas").classes(
                                "text-caption text-gray-400"
                            )
                            ui.label(
                                str(stats["gestiones_activas"])
                            ).classes("text-h4 font-bold")

                # Tarjeta total pagos
                with ui.card().classes("flex-1 p-4"):
                    with ui.row().classes("items-center gap-3"):
                        ui.icon(
                            "payments", size="2.5rem"
                        ).classes("text-secondary")
                        with ui.column().classes("gap-0"):
                            ui.label("Total Pagos").classes(
                                "text-caption text-gray-400"
                            )
                            ui.label(
                                str(stats["total_pagos"])
                            ).classes("text-h4 font-bold")

                # Tarjeta importe total
                with ui.card().classes("flex-1 p-4"):
                    with ui.row().classes("items-center gap-3"):
                        ui.icon(
                            "attach_money", size="2.5rem"
                        ).classes("text-accent")
                        with ui.column().classes("gap-0"):
                            ui.label("Importe Total").classes(
                                "text-caption text-gray-400"
                            )
                            ui.label(
                                f"${stats['total_importe']:,.2f}"
                            ).classes("text-h4 font-bold")

            # Tarjetas de suma por forma de pago
            if stats["formas_pago"]:
                ui.label("💳 Totales por Forma de Pago").classes(
                    "text-h6 mt-2 mb-2"
                )
                with ui.row().classes(
                    "w-full gap-4 mb-4 flex-wrap"
                ):
                    for fp in stats["formas_pago"]:
                        with ui.card().classes("p-4"):
                            with ui.column().classes("gap-1"):
                                ui.label(
                                    fp["forma_pago"]
                                    or "Sin especificar"
                                ).classes(
                                    "text-subtitle2 font-bold"
                                )
                                ui.label(
                                    f"Pagos: {fp['cantidad_pagos']}"
                                ).classes(
                                    "text-caption text-gray-400"
                                )
                                ui.label(
                                    f"${fp['importe_total']:,.2f}"
                                ).classes(
                                    "text-body1 text-primary font-bold"
                                )

            ui.separator().classes("my-4")

            # Crear tabs
            with ui.tabs().classes("w-full") as tabs:
                tab1 = ui.tab("📋 Formas de Pago", icon="payment")
                tab2 = ui.tab(
                    "👥 Pagadores y Destinatarios", icon="people"
                )
                tab3 = ui.tab(
                    "🔍 Comparación SM", icon="compare_arrows"
                )

            with ui.tab_panels(tabs, value=tab1).classes(
                "w-full"
            ):
                # Panel 1: Formas de Pago
                with ui.tab_panel(tab1):
                    if len(df_pagos) > 0:
                        # Crear y mostrar gráfico de formas de pago
                        fig = crear_grafico_pagos_por_mes(
                            df_pagos
                        )

                        with ui.card().classes("w-full p-4"):
                            ui.label(
                                "Análisis de Pagos por Forma de Pago"
                            ).classes("text-h5 mb-4")
                            ui.plotly(fig).classes("w-full")
                    else:
                        with ui.card().classes(
                            "w-full p-8 text-center"
                        ):
                            ui.icon("info", size="3rem").classes(
                                "text-warning"
                            )
                            ui.label(
                                "No hay datos de formas de pago"
                            ).classes("text-h6 q-mt-md")

                # Panel 2: Pagadores y Destinatarios
                with ui.tab_panel(tab2):
                    if len(df_agentes) > 0:
                        # Crear y mostrar gráfico de agentes
                        fig_agentes = crear_grafico_pagos_agentes(
                            df_agentes
                        )

                        with ui.card().classes("w-full p-4"):
                            ui.label(
                                "Análisis de Pagos por Pagador y Destinatario"
                            ).classes("text-h5 mb-4")
                            ui.plotly(fig_agentes).classes(
                                "w-full"
                            )
                    else:
                        with ui.card().classes(
                            "w-full p-8 text-center"
                        ):
                            ui.icon("info", size="3rem").classes(
                                "text-warning"
                            )
                            ui.label(
                                "No hay datos de agentes"
                            ).classes("text-h6 q-mt-md")

                # Panel 3: Comparación SM
                with ui.tab_panel(tab3):
                    if (
                        len(df_sm_pagador) > 0
                        or len(df_sm_destinatario) > 0
                    ):
                        # Crear y mostrar gráfico comparativo
                        fig_sm = crear_grafico_comparacion_sm(
                            df_sm_pagador, df_sm_destinatario
                        )

                        with ui.card().classes("w-full p-4"):
                            ui.label(
                                "Comparación SM: Pagador vs Destinatario"
                            ).classes("text-h5 mb-4")
                            ui.plotly(fig_sm).classes("w-full")
                    else:
                        with ui.card().classes(
                            "w-full p-8 text-center"
                        ):
                            ui.icon("info", size="3rem").classes(
                                "text-warning"
                            )
                            ui.label(
                                "No hay datos de SM"
                            ).classes("text-h6 q-mt-md")

            # Mostrar mensaje si no hay datos en ningún reporte
            if (
                len(df_pagos) == 0
                and len(df_agentes) == 0
                and len(df_sm_pagador) == 0
                and len(df_sm_destinatario) == 0
            ):
                with ui.card().classes(
                    "w-full p-8 text-center mt-4"
                ):
                    ui.icon("info", size="3rem").classes(
                        "text-warning"
                    )
                    ui.label("No hay datos disponibles").classes(
                        "text-h6 q-mt-md"
                    )
                    ui.label(
                        "Aún no hay pagos registrados en gestiones activas"
                    ).classes("text-gray-500")

        except Exception as e:
            with ui.card().classes("w-full p-8 text-center"):
                ui.icon("error", size="3rem").classes(
                    "text-negative"
                )
                ui.label("Error al cargar reportes").classes(
                    "text-h6 q-mt-md"
                )
                ui.label(f"Error: {str(e)}").classes(
                    "text-gray-500"
                )
