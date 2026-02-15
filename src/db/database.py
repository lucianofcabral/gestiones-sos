import os
import sqlite3
from pathlib import Path
import datetime
from src.commons import SQL_CREATE_FILE, DB_PATH, ACCESS_DB_PATH
import pyodbc


class SQLiteDB:
    def __init__(self):
        self.conn = sqlite3.connect(
            DB_PATH, check_same_thread=False
        )
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def migrar(self):
        try:
            self.cursor.execute("Select * from gestiones")
            print("Ya existe la DB")
            return
        except Exception:
            import polars as pl

            # Crear base de datos
            with open(SQL_CREATE_FILE, "r") as f:
                sentencias = f.read()
                for s in sentencias.split("--"):
                    try:
                        self.cursor.execute("--" + s)
                    except Exception as e:
                        print(s)
                        print(e)
            conn_str = (
                r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
                rf"Dbq={ACCESS_DB_PATH};"
            )

            # Leer dataframes
            def get_polars_from_table(
                tabla: str,
            ) -> pl.DataFrame:
                if os.name == "nt":
                    query: str = f"Select * from {tabla} ;"
                    with pyodbc.connect(conn_str) as cn:
                        cur = cn.cursor()
                        cur.execute(query)
                        rows = cur.execute(query).fetchall()
                        cols = [
                            column[0]
                            for column in cur.description
                        ]
                        data: list[dict] = [
                            dict(zip(cols, row)) for row in rows
                        ]
                        dataframe: pl.DataFrame = pl.from_dicts(
                            data
                        )
                else:
                    import subprocess
                    from io import StringIO

                    result = subprocess.run(
                        ["mdb-export", ACCESS_DB_PATH, tabla],
                        capture_output=True,
                        text=True,
                        check=True,
                    )

                    # Leer CSV directamente con Polars
                    dataframe: pl.DataFrame = pl.read_csv(
                        StringIO(result.stdout)
                    )

                return dataframe

            facturas = get_polars_from_table("Facturas")
            tres_arr = get_polars_from_table("TresArroyos")
            formas_pago = get_polars_from_table("catFormasDePago")
            # cat_gestiones = get_polars_from_table("catEstadoGestiones")
            destinatarios = get_polars_from_table(
                "catDestinatarios"
            )
            pagadores = get_polars_from_table("catPagadores")
            estados = get_polars_from_table("catEstadoGestiones")

            notas = get_polars_from_table("NotasDeCredito")
            gestiones = get_polars_from_table("Gestiones")
            pagos = get_polars_from_table("Pagos")

            # INserciones
            #  Formas de Pago

            for row in formas_pago.to_dicts():
                self.cursor.execute(
                    "Insert into formaspago (formapago) values (:formapago);",
                    {
                        "formapago": str(row["FormaDePago"])
                        .strip()
                        .title(),
                    },
                )
                ewid = self.cursor.lastrowid
                aux_sql = "Insert into aux_formaspago (id_viejo,id_nuevo) values (:id_viejo, :id_nuevo);"
                self.cursor.execute(
                    aux_sql,
                    {
                        "id_viejo": row["Id"],
                        "id_nuevo": ewid,
                    },
                )

            # Agentes
            agentes = destinatarios.join(
                pagadores,
                how="left",
                left_on="Destinatario",
                right_on="Pagador",
            ).select(
                [
                    pl.col("ID").alias("id_destinatario"),
                    pl.when(
                        pl.col("Destinatario").str.len_chars() > 3
                    )
                    .then(
                        pl.col("Destinatario").str.to_titlecase()
                    )
                    .otherwise(pl.col("Destinatario"))
                    .str.strip_chars()
                    .alias("agente"),
                    pl.col("Id").alias("id_pagador"),
                ]
            )
            for row in agentes.to_dicts():
                self.cursor.execute(
                    "Insert into agentes (agente) values (:agente);",
                    {"agente": str(row["agente"])},
                )
                ewid = self.cursor.lastrowid
                aux_sql = "Insert into aux_agentes (id_destinatario,id_pagador,id_nuevo) values (:id_destinatario,:id_pagador,:id_nuevo);"
                self.cursor.execute(
                    aux_sql,
                    {
                        "id_destinatario": row["id_destinatario"],
                        "id_pagador": row["id_pagador"],
                        "id_nuevo": ewid,
                    },
                )

            # facturas
            facturas_data = facturas.select(
                [
                    pl.col(col).alias(col.lower())
                    for col in facturas.columns
                ]
            ).select(
                [
                    "id",
                    pl.col("fechaemitida")
                    .str.to_date(format="%m/%d/%y %H:%M:%S")
                    .dt.strftime("%Y-%m-%d"),
                    pl.col("periodo")
                    .str.to_date(format="%m/%d/%y %H:%M:%S")
                    .dt.strftime("%Y%m"),
                    pl.col("importe").cast(pl.Float32),
                ]
            )

            for row in facturas_data.to_dicts():
                self.cursor.execute(
                    "Insert into facturas (fechaemitida,periodo,importe) values (:fechaemitida,:periodo,:importe);",
                    {
                        "fechaemitida": str(row["fechaemitida"]),
                        "periodo": str(row["periodo"]),
                        "importe": row["importe"],
                    },
                )
                ewid = self.cursor.lastrowid
                aux_sql = "Insert into aux_facturas (id_viejo,id_nuevo) values (:id_viejo,:id_nuevo);"
                self.cursor.execute(
                    aux_sql,
                    {
                        "id_viejo": row["id"],
                        "id_nuevo": ewid,
                    },
                )

            colorder = gestiones.columns + ["IdGestion3A"]

            # gestiones
            gestiones_concatenado = pl.concat(
                [
                    gestiones.join(
                        estados.with_columns(
                            pl.col("Estado")
                            .str.strip_chars()
                            .str.to_titlecase()
                        ),
                        how="left",
                        left_on="Estado",
                        right_on="id",
                    )
                    .drop("Estado")
                    .rename({"Estado_right": "Estado"})
                    .with_columns(
                        [
                            pl.col("Fecha")
                            .str.to_date(
                                format="%m/%d/%y %H:%M:%S"
                            )
                            .dt.strftime("%Y-%m-%d"),
                            pl.col("Poliza")
                            .cast(pl.Int64)
                            .cast(pl.String),
                            pl.col("TotalFactura").cast(
                                pl.Float32
                            ),
                            pl.col("FechaTerminado")
                            .str.to_date(
                                format="%m/%d/%y %H:%M:%S"
                            )
                            .dt.strftime("%Y-%m-%d"),
                            pl.col("Activa").cast(pl.Int64),
                            pl.col("Terminado").cast(pl.Int64),
                            pl.lit(None)
                            .alias("IdGestion3A")
                            .cast(pl.Int64),
                        ]
                    )
                    .select(colorder),
                    tres_arr.sort(["Fecha", "NroFactura"])
                    .select(
                        [
                            pl.lit(0)
                            .alias("NGestion")
                            .cast(pl.Int64),
                            pl.col("Fecha")
                            .str.to_date(
                                format="%m/%d/%y %H:%M:%S"
                            )
                            .dt.strftime("%Y-%m-%d"),
                            pl.lit("")
                            .alias("Cliente")
                            .cast(pl.String),
                            "Dominio",
                            pl.col("Poliza")
                            .cast(pl.Int64)
                            .cast(pl.String),
                            pl.lit("Especial")
                            .alias("Tipo")
                            .cast(pl.String),
                            pl.lit("")
                            .alias("Motivo")
                            .cast(pl.String),
                            pl.lit(0)
                            .alias("NCaso")
                            .cast(pl.Int64),
                            pl.lit("")
                            .alias("UsuarioCarga")
                            .cast(pl.String),
                            pl.lit("")
                            .alias("UsuarioRespuesta")
                            .cast(pl.String),
                            pl.lit("Cerrada")
                            .alias("Estado")
                            .cast(pl.String),
                            pl.lit(0).alias("ITR").cast(pl.Int64),
                            pl.lit("")
                            .alias("RutaCarpeta")
                            .cast(pl.String),
                            pl.col("Importe")
                            .alias("TotalFactura")
                            .cast(pl.Float32),
                            pl.lit(1)
                            .cast(pl.Int64)
                            .alias("Terminado"),
                            pl.col("Fecha")
                            .str.to_date(
                                format="%m/%d/%y %H:%M:%S"
                            )
                            .dt.strftime("%Y-%m-%d")
                            .alias("FechaTerminado"),
                            "Obs",
                            pl.lit(1)
                            .cast(pl.Int64)
                            .alias("Activa"),
                            pl.col("Id").alias("IdGestion3A"),
                        ]
                    )
                    .select(colorder),
                ]
            )
            gestiones_concatenado = (
                gestiones_concatenado.select(
                    [
                        pl.col(col).alias(col.lower())
                        for col in gestiones_concatenado.columns
                    ]
                )
                .with_columns(
                    [
                        pl.col("dominio").str.replace_all(
                            " ", ""
                        ),
                    ]
                )
                .select(pl.exclude("fechaterminado"))
            )

            cols = [
                c
                for c in list(gestiones_concatenado.columns)
                if c not in ["idgestion3a", "rutacarpeta"]
            ]
            col_list = ", ".join(cols)
            placeholders = ",".join(f":{c}" for c in cols)
            sql = f"Insert Into gestiones ({col_list}) Values ({placeholders});"
            for row in gestiones_concatenado.to_dicts():
                params = {c: row.get(c) for c in cols}
                self.cursor.execute(sql, params)
                newid = self.cursor.lastrowid
                aux_sql = "Insert into aux_gestiones (ngestion,id_viejo,id_nuevo) values (:ngestion, :id_viejo, :id_nuevo);"
                self.cursor.execute(
                    aux_sql,
                    {
                        "ngestion": row["ngestion"] or 0,
                        "id_viejo": row["idgestion3a"] or 0,
                        "id_nuevo": newid or 0,
                    },
                )

            # Pagos
            pagos_data = pl.concat(
                [
                    (
                        pagos.filter(pl.col("NGestion") > 0)
                        .with_columns(
                            pl.col("Fecha")
                            .str.to_date(
                                format="%m/%d/%y %H:%M:%S"
                            )
                            .dt.strftime("%Y-%m-%d")
                        )
                        .with_columns(
                            pl.lit(0)
                            .alias("id_gestion")
                            .cast(pl.Int64)
                        )
                    ),
                    pagos.join(
                        tres_arr.select(
                            [
                                pl.col("Id").alias("id_gestion"),
                                "IdPago",
                            ]
                        ),
                        how="inner",
                        left_on="id",
                        right_on="IdPago",
                    ).with_columns(
                        pl.col("Fecha")
                        .str.to_date(format="%m/%d/%y %H:%M:%S")
                        .dt.strftime("%Y-%m-%d")
                    ),
                ]
            )

            pagos_data = (
                pagos_data.select(
                    [
                        pl.col(col).alias(col.lower())
                        for col in pagos_data.columns
                    ]
                )
                .sort("fecha")
                .with_columns(
                    [
                        pl.col("formadepago").fill_null(1),
                        pl.col("importe").cast(pl.Float64).abs(),
                    ]
                )
            )
            for row in pagos_data.to_dicts():
                ngestion = row["ngestion"] or 0
                idgestion = row["id_gestion"] or 0
                try:
                    if ngestion > 0:
                        gid = self.cursor.execute(
                            "Select id_nuevo from aux_gestiones where ngestion = :ngestion;",
                            {"ngestion": ngestion},
                        ).fetchone()[0]
                    elif idgestion > 0:
                        gid = self.cursor.execute(
                            "Select id_nuevo from aux_gestiones where id_viejo = :id_viejo;",
                            {"id_viejo": idgestion},
                        ).fetchone()[0]
                    else:
                        gid = None

                    if gid is None:
                        raise ValueError(
                            f"Error: No se encontró ngestion ni id_gestion -- {row}"
                        )

                    fpid = self.cursor.execute(
                        "Select id_nuevo from aux_formaspago where id_viejo = :id_viejo;",
                        {"id_viejo": row["formadepago"]},
                    ).fetchone()[0]
                    agpagid = self.cursor.execute(
                        "Select id_nuevo from aux_agentes where id_pagador = :id_pagador;",
                        {"id_pagador": row["pagador"]},
                    ).fetchone()[0]
                    agdestid = self.cursor.execute(
                        "Select id_nuevo from aux_agentes where id_destinatario = :id_destinatario;",
                        {"id_destinatario": row["destinatario"]},
                    ).fetchone()[0]

                    d = {
                        "gestion_id": gid,
                        "fecha": row["fecha"],
                        "pagador_id": agpagid,
                        "destinatario_id": agdestid,
                        "formapago_id": fpid,
                        "importe": row["importe"],
                    }
                    self.cursor.execute(
                        """Insert into pagos 
                            (gestion_id,fecha,pagador_id,destinatario_id,formapago_id,importe) 
                            values (:gestion_id,:fecha,:pagador_id,:destinatario_id,:formapago_id,:importe);""",
                        d,
                    )
                    newid = self.cursor.lastrowid
                    self.cursor.execute(
                        "Insert into aux_pagos (id_viejo,id_nuevo) values (:id_viejo, :id_nuevo);",
                        {
                            "id_viejo": row["id"],
                            "id_nuevo": newid,
                        },
                    )

                except Exception as e:
                    print(f"Error procesando pago: {row}\n{e}")
                    break

            # Notas
            notas_data = notas.with_columns(
                pl.col("FechaPasada")
                .str.to_date(format="%m/%d/%y %H:%M:%S")
                .dt.strftime("%Y-%m-%d")
            ).sort("IdPago")
            notas_data = notas_data.select(
                [
                    pl.col(col).alias(col.lower())
                    for col in notas_data.columns
                ]
            ).select(pl.exclude("pasada"))

            for row in notas_data.to_dicts():
                try:
                    pagoid = 0
                    factid = None
                    pagoid = self.cursor.execute(
                        "Select id_nuevo from aux_pagos where id_viejo = :id_viejo;",
                        {"id_viejo": row["idpago"]},
                    ).fetchone()[0]
                    try:
                        factid = self.cursor.execute(
                            "Select id_nuevo from aux_facturas where id_viejo = :id_viejo;",
                            {"id_viejo": row["idfactura"]},
                        ).fetchone()[0]
                    except Exception:
                        factid = None

                    self.cursor.execute(
                        "Insert into notas (pago_id,factura_id) values (:pago_id,:factura_id);",
                        {
                            "pago_id": pagoid,
                            "factura_id": factid,
                        },
                    )
                except Exception as e:
                    print(
                        f"Error procesando nota: {row}\n {(pagoid, factid)} \n{e}"
                    )
                    continue

        self.conn.commit()

    # Get functions
    def obtener_tipos(self) -> list[str]:
        self.cursor.execute(
            "SELECT DISTINCT tipo FROM gestiones ORDER BY tipo;"
        )
        rows = self.cursor.fetchall()
        return [dict(row).get("tipo", "") for row in rows]

    def obtener_agentes(self) -> list[str]:
        self.cursor.execute(
            "SELECT agente FROM agentes ORDER BY agente;"
        )
        rows = self.cursor.fetchall()
        return [dict(row).get("agente", "") for row in rows]

    def obtener_formaspago(self) -> list[str]:
        self.cursor.execute(
            "SELECT formapago FROM formaspago ORDER BY formapago;"
        )
        rows = self.cursor.fetchall()
        return [dict(row).get("formapago", "") for row in rows]

    def filter_gestiones(
        self,
        texto_busqueda: str,
        tipo: str,
        terminado: bool,
        no_terminado: bool,
        activa: bool,
        no_activa: bool,
        con_pagos: bool,
        sin_pagos: bool,
        con_nota: bool,
        sin_nota: bool,
        con_nota_pasada: bool,
    ) -> list[dict[str, any]]:
        query = "Select * from gestiones g Where 1=1"
        params: dict = {}

        if tipo and tipo != "all":
            query += " AND g.tipo = :tipo"
            params.update({"tipo": tipo})

        if texto_busqueda:
            query += """ AND (
                    g.ngestion LIKE :t
                    OR g.cliente LIKE :t
                    OR g.dominio LIKE :t
                    OR g.poliza LIKE :t
                    OR g.obs LIKE :t
                    )"""
            params.update({"t": f"%{texto_busqueda}%"})

        if activa and (not no_activa):
            query += " AND g.activa = 1"
        elif no_activa and (not activa):
            query += " AND g.activa = 0"

        if terminado and (not no_terminado):
            query += " AND g.terminado = 1"
        elif no_terminado and (not terminado):
            query += " AND g.terminado = 0"

        if con_pagos and (not sin_pagos):
            query += """ AND EXISTS (
                    Select p.id
                    from pagos p
                    where g.id = p.gestion_id
            )"""
        elif sin_pagos and (not con_pagos):
            query += """ AND NOT EXISTS (
                    Select p.id
                    from pagos p
                    where g.id = p.gestion_id
            )"""

        if con_nota and (not sin_nota):
            query += """ AND EXISTS (
                    Select p.id
                    from pagos p
                    where g.id = p.gestion_id
                        and Exists (
                            Select n.id
                            from notas n
                            where n.pago_id = p.id
                        )
            )"""
        elif sin_nota and (not con_nota):
            query += """ AND NOT EXISTS (
                    Select p.id
                    from pagos p
                    where g.id = p.gestion_id
                        and Exists (
                            Select n.id
                            from notas n
                            where n.pago_id = p.id
                        )
            )"""

        if con_nota_pasada:
            query += """ AND EXISTS (
                    Select p.id
                    from pagos p
                    where g.id = p.gestion_id
                        and Exists (
                            Select n.id
                            from notas n
                            where n.pago_id = p.id
                                and n.factura_id IS NOT NULL
                        )
            )"""

        query += " ORDER BY g.fecha DESC"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def filtrar_pagos(
        self,
        texto_busqueda: str,
        pagador: str,
        destinatario: str,
        formapago: str,
        es_nota_credito_no_pasada: bool,
    ) -> list[dict[str, any]]:
        query = """SELECT
                        p.id,
                        p.fecha,
                        ap.agente AS pagador,
                        ad.agente AS destinatario,
                        fp.formapago,
                        p.importe,
                        g.tipo,
                        g.ngestion,
                        g.dominio ,
                        g.poliza ,
                        g.cliente ,
                        ((n.id IS NOT NULL) and
                        (f.id IS NULL)) AS es_nota_credito_no_pasada
                    FROM
                        pagos p
                    LEFT JOIN agentes ap ON
                        p.pagador_id = ap.id
                    LEFT JOIN agentes ad ON
                        p.destinatario_id = ad.id
                    LEFT JOIN formaspago fp ON
                        p.formapago_id = fp.id
                    LEFT JOIN gestiones g ON
                        p.gestion_id = g.id
                    LEFT JOIN notas n ON
                        p.id = n.pago_id
                    LEFT JOIN facturas f ON
                        n.factura_id = f.id 
                    WHERE 1=1"""
        params = {}

        if texto_busqueda:
            query += """ AND (
                ngestion LIKE :texto 
                OR dominio LIKE :texto 
                OR poliza LIKE :texto
                OR cliente LIKE :texto
                OR pagador LIKE :texto
                OR destinatario LIKE :texto
                OR formapago LIKE :texto
                )"""
            params.update({"texto": f"%{texto_busqueda}%"})

        if pagador and pagador != "all":
            query += " AND pagador = :pagador"
            params.update({"pagador": pagador})

        if destinatario and destinatario != "all":
            query += " AND destinatario = :destinatario"
            params.update({"destinatario": destinatario})

        if formapago and formapago != "all":
            query += " AND formapago = :formapago"
            params.update({"formapago": formapago})

        if es_nota_credito_no_pasada:
            query += (
                " AND ((n.id IS NOT NULL) AND (f.id IS NULL))"
            )

        query += " ORDER BY p.fecha DESC"

        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def obtener_pagos_por_gestion(
        self, gestion_id: int
    ) -> list[dict[str, any]]:
        """Obtiene todos los pagos de una gestión específica"""
        query = """SELECT
                        p.id,
                        p.fecha,
                        ap.agente AS pagador,
                        ad.agente AS destinatario,
                        fp.formapago,
                        p.importe,
                        ((n.id IS NOT NULL) and
                        (f.id IS NULL)) AS es_nota_credito_no_pasada
                    FROM
                        pagos p
                    LEFT JOIN agentes ap ON
                        p.pagador_id = ap.id
                    LEFT JOIN agentes ad ON
                        p.destinatario_id = ad.id
                    LEFT JOIN formaspago fp ON
                        p.formapago_id = fp.id
                    LEFT JOIN notas n ON
                        p.id = n.pago_id
                    LEFT JOIN facturas f ON
                        n.factura_id = f.id 
                    WHERE p.gestion_id = :gestion_id
                    ORDER BY p.fecha DESC"""

        self.cursor.execute(query, {"gestion_id": gestion_id})
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def obtener_pago_por_id(self, pago_id: int) -> dict:
        """Obtiene un pago específico por ID"""
        try:
            query = """
            SELECT 
                p.id,
                p.fecha,
                a1.agente as pagador,  -- Cambié 'nombre' por 'agente'
                a2.agente as destinatario,  -- Cambié 'nombre' por 'agente' 
                fp.formapago as formapago,  -- Cambié 'nombre' por 'formapago'
                p.importe,
                g.tipo,
                g.ngestion,
                g.dominio,
                g.poliza,
                g.cliente,
                CASE WHEN EXISTS(
                    SELECT 1 FROM notas n WHERE n.pago_id = p.id AND n.factura_id IS NULL
                ) THEN 1 ELSE 0 END as es_nota_credito_no_pasada
            FROM pagos p
            LEFT JOIN gestiones g ON p.gestion_id = g.id
            LEFT JOIN agentes a1 ON p.pagador_id = a1.id
            LEFT JOIN agentes a2 ON p.destinatario_id = a2.id
            LEFT JOIN formaspago fp ON p.formapago_id = fp.id
            WHERE p.id = :pago_id
            """

            result = self.cursor.execute(
                query, {"pago_id": pago_id}
            ).fetchone()
            if result:
                return dict(result)
            return {}
        except Exception as e:
            print(f"Error obteniendo pago: {e}")
            return {}

    def obtener_gestion_por_id(self, gestion_id: int) -> dict:
        """Obtiene una gestión específica por ID"""
        try:
            query = """
            SELECT * FROM gestiones WHERE id = :gestion_id
            """
            result = self.cursor.execute(
                query, {"gestion_id": gestion_id}
            ).fetchone()
            if result:
                return dict(result)
            return {}
        except Exception as e:
            print(f"Error obteniendo gestión: {e}")
            return {}

    # Do functions

    def actualizar_pago(
        self,
        pago_id: int,
        new_fecha: str,
        new_pagador: str,
        new_destinatario: str,
        new_formapago: str,
        new_importe: float,
    ) -> tuple[bool, str]:
        """
        Actualiza un pago en la base de datos de forma transaccional.
        Gestiona automáticamente las notas de crédito y aplica las reglas de negocio.

        Args:
            pago_id: ID del pago a actualizar
            new_fecha: Nueva fecha en formato YYYY-MM-DD
            new_pagador: Nombre del nuevo pagador
            new_destinatario: Nombre del nuevo destinatario
            new_formapago: Nueva forma de pago
            new_importe: Nuevo importe

        Returns:
            tuple[bool, str]: (éxito, mensaje descriptivo)
        """
        try:
            # Iniciar transacción explícita
            self.cursor.execute("BEGIN TRANSACTION")

            # Obtener pago actual
            old_pago = self.obtener_pago_por_id(pago_id)
            if not old_pago:
                self.conn.rollback()
                return False, "Pago no encontrado"

            old_formapago = old_pago.get("formapago", "")

            # Verificar si hay nota existente y su estado
            old_nota = self.cursor.execute(
                "SELECT * FROM notas WHERE pago_id = :pago_id",
                {"pago_id": pago_id},
            ).fetchone()
            old_nota = dict(old_nota) if old_nota else {}
            old_nota_pasada = (
                old_nota.get("factura_id") is not None
                if old_nota
                else False
            )

            # Validar y formatear fecha
            try:
                fecha_formateada = (
                    datetime.datetime.strptime(
                        new_fecha, "%Y-%m-%d"
                    )
                    .date()
                    .isoformat()
                )
            except ValueError:
                self.conn.rollback()
                return (
                    False,
                    f"Formato de fecha inválido: {new_fecha}",
                )

            # Determinar pagador y destinatario según reglas de negocio
            if new_formapago == "Nota De Credito":
                # Si es nota de crédito: forzar SOS y SM
                pagador_id = self.obtener_agente_id_por_nombre(
                    "SOS"
                )
                destinatario_id = (
                    self.obtener_agente_id_por_nombre("SM")
                )

                if pagador_id is None:
                    self.conn.rollback()
                    return (
                        False,
                        "Agente 'SOS' no encontrado en la base de datos",
                    )
                if destinatario_id is None:
                    self.conn.rollback()
                    return (
                        False,
                        "Agente 'SM' no encontrado en la base de datos",
                    )

            else:
                # Si no es nota de crédito: usar los valores proporcionados
                pagador_id = self.obtener_agente_id_por_nombre(
                    new_pagador
                )
                destinatario_id = (
                    self.obtener_agente_id_por_nombre(
                        new_destinatario
                    )
                )

                if pagador_id is None:
                    self.conn.rollback()
                    return (
                        False,
                        f"Pagador no encontrado: {new_pagador}",
                    )
                if destinatario_id is None:
                    self.conn.rollback()
                    return (
                        False,
                        f"Destinatario no encontrado: {new_destinatario}",
                    )

            # Obtener ID de forma de pago
            formapago_id = self.obtener_formapago_id_por_nombre(
                new_formapago
            )
            if formapago_id is None:
                self.conn.rollback()
                return (
                    False,
                    f"Forma de pago no encontrada: {new_formapago}",
                )

            # Actualizar el pago
            query = """
            UPDATE pagos 
            SET fecha = :fecha,
                pagador_id = :pagador_id,
                destinatario_id = :destinatario_id,
                formapago_id = :formapago_id,
                importe = :importe
            WHERE id = :pago_id
            """

            self.cursor.execute(
                query,
                {
                    "pago_id": pago_id,
                    "fecha": fecha_formateada,
                    "pagador_id": pagador_id,
                    "destinatario_id": destinatario_id,
                    "formapago_id": formapago_id,
                    "importe": float(new_importe),
                },
            )

            # Gestionar tabla notas según cambios en forma de pago
            cambio_a_nota = (
                old_formapago != "Nota De Credito"
                and new_formapago == "Nota De Credito"
            )
            cambio_desde_nota = (
                old_formapago == "Nota De Credito"
                and new_formapago != "Nota De Credito"
            )

            mensaje = "Pago actualizado correctamente"

            if cambio_a_nota:
                # Cambió A Nota De Crédito: crear registro en tabla notas
                existing = self.cursor.execute(
                    "SELECT id FROM notas WHERE pago_id = :pago_id",
                    {"pago_id": pago_id},
                ).fetchone()

                if not existing:
                    self.cursor.execute(
                        "INSERT INTO notas (pago_id, factura_id, pasada) VALUES (:pago_id, NULL, 0)",
                        {"pago_id": pago_id},
                    )
                    mensaje = "Pago actualizado y nota de crédito creada"

            elif cambio_desde_nota:
                # Cambió DESDE Nota De Crédito: verificar y eliminar si es posible
                if old_nota_pasada:
                    self.conn.rollback()
                    return (
                        False,
                        "No se puede cambiar la forma de pago: la nota de crédito tiene factura asociada",
                    )

                # Eliminar solo si factura_id es NULL
                self.cursor.execute(
                    "DELETE FROM notas WHERE pago_id = :pago_id AND factura_id IS NULL",
                    {"pago_id": pago_id},
                )
                mensaje = (
                    "Pago actualizado y nota de crédito eliminada"
                )

            # Si todo salió bien, hacer commit
            self.conn.commit()
            return True, mensaje

        except Exception as e:
            # Si hay cualquier error, revertir todo
            self.conn.rollback()
            print(f"Error actualizando pago: {e}")
            return False, f"Error: {str(e)}"

    def crear_pago(
        self,
        gestion_id: int,
        fecha: str,
        pagador: str,
        destinatario: str,
        formapago: str,
        importe: float,
    ) -> tuple[bool, str]:
        """
        Crea un nuevo pago en la base de datos de forma transaccional.
        Gestiona automáticamente las notas de crédito y aplica las reglas de negocio.

        Args:
            gestion_id: ID de la gestión asociada
            fecha: Fecha del pago en formato YYYY-MM-DD
            pagador: Nombre del pagador
            destinatario: Nombre del destinatario
            formapago: Forma de pago
            importe: Importe del pago

        Returns:
            tuple[bool, str]: (éxito, mensaje descriptivo)
        """
        try:
            # Iniciar transacción explícita
            self.cursor.execute("BEGIN TRANSACTION")

            # Validar que existe la gestión
            gestion = self.cursor.execute(
                "SELECT id FROM gestiones WHERE id = :gestion_id",
                {"gestion_id": gestion_id},
            ).fetchone()

            if not gestion:
                self.conn.rollback()
                return (
                    False,
                    f"Gestión con ID {gestion_id} no encontrada",
                )

            # Validar y formatear fecha
            try:
                fecha_formateada = (
                    datetime.datetime.strptime(fecha, "%Y-%m-%d")
                    .date()
                    .isoformat()
                )
            except ValueError:
                self.conn.rollback()
                return (
                    False,
                    f"Formato de fecha inválido: {fecha}",
                )

            # Validar importe
            if importe <= 0:
                self.conn.rollback()
                return False, "El importe debe ser mayor a 0"

            # Determinar pagador y destinatario según reglas de negocio
            if formapago == "Nota De Credito":
                # Si es nota de crédito: forzar SOS y SM
                pagador_id = self.obtener_agente_id_por_nombre(
                    "SOS"
                )
                destinatario_id = (
                    self.obtener_agente_id_por_nombre("SM")
                )

                if pagador_id is None:
                    self.conn.rollback()
                    return (
                        False,
                        "Agente 'SOS' no encontrado en la base de datos",
                    )
                if destinatario_id is None:
                    self.conn.rollback()
                    return (
                        False,
                        "Agente 'SM' no encontrado en la base de datos",
                    )
            else:
                # Si no es nota de crédito: usar los valores proporcionados
                pagador_id = self.obtener_agente_id_por_nombre(
                    pagador
                )
                destinatario_id = (
                    self.obtener_agente_id_por_nombre(
                        destinatario
                    )
                )

                if pagador_id is None:
                    self.conn.rollback()
                    return (
                        False,
                        f"Pagador no encontrado: {pagador}",
                    )
                if destinatario_id is None:
                    self.conn.rollback()
                    return (
                        False,
                        f"Destinatario no encontrado: {destinatario}",
                    )

            # Obtener ID de forma de pago
            formapago_id = self.obtener_formapago_id_por_nombre(
                formapago
            )
            if formapago_id is None:
                self.conn.rollback()
                return (
                    False,
                    f"Forma de pago no encontrada: {formapago}",
                )

            # Insertar el pago
            query = """
            INSERT INTO pagos (gestion_id, fecha, pagador_id, destinatario_id, formapago_id, importe)
            VALUES (:gestion_id, :fecha, :pagador_id, :destinatario_id, :formapago_id, :importe)
            """

            self.cursor.execute(
                query,
                {
                    "gestion_id": gestion_id,
                    "fecha": fecha_formateada,
                    "pagador_id": pagador_id,
                    "destinatario_id": destinatario_id,
                    "formapago_id": formapago_id,
                    "importe": float(importe),
                },
            )

            nuevo_pago_id = self.cursor.lastrowid
            mensaje = "Pago creado correctamente"

            # Si es Nota De Crédito, crear registro en tabla notas
            if formapago == "Nota De Credito":
                self.cursor.execute(
                    "INSERT INTO notas (pago_id, factura_id, pasada) VALUES (:pago_id, NULL, 0)",
                    {"pago_id": nuevo_pago_id},
                )
                mensaje = (
                    "Pago y nota de crédito creados correctamente"
                )

            # Si todo salió bien, hacer commit
            self.conn.commit()
            return True, mensaje

        except Exception as e:
            # Si hay cualquier error, revertir todo
            self.conn.rollback()
            print(f"Error creando pago: {e}")
            return False, f"Error: {str(e)}"

    def eliminar_pago(self, pago_id: int) -> bool:
        """Elimina un pago de la base de datos"""
        try:
            self.cursor.execute(
                "DELETE FROM pagos WHERE id = :pago_id",
                {"pago_id": pago_id},
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error eliminando pago: {e}")
            return False

    def obtener_agente_id_por_nombre(
        self, nombre: str
    ) -> int | None:
        """Obtiene el ID de un agente por su nombre"""
        try:
            result = self.cursor.execute(
                "SELECT id FROM agentes WHERE agente = :agente",
                {"agente": nombre},
            ).fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error obteniendo agente: {e}")
            return None

    def obtener_formapago_id_por_nombre(
        self, nombre: str
    ) -> int | None:
        """Obtiene el ID de una forma de pago por su nombre"""
        try:
            result = self.cursor.execute(
                "SELECT id FROM formaspago WHERE formapago = :formapago",
                {"formapago": nombre},
            ).fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error obteniendo forma de pago: {e}")
            return None

    def crear_gestion(
        self,
        ngestion: int,
        fecha: str,
        cliente: str,
        dominio: str,
        poliza: str,
        tipo: str,
        motivo: str,
        ncaso: int,
        usuariocarga: str,
        usuariorespuesta: str,
        estado: int,
        itr: int,
        totalfactura: float,
        terminado: int,
        obs: str,
        activa: int,
    ) -> tuple[bool, str]:
        """
        Crea una nueva gestión en la base de datos.

        Returns:
            tuple[bool, str]: (éxito, mensaje descriptivo)
        """
        try:
            # Validar campos requeridos
            if not poliza:
                return False, "La póliza es obligatoria"

            if not tipo:
                return False, "El tipo es obligatorio"

            # Validar y formatear fecha
            try:
                fecha_formateada = (
                    datetime.datetime.strptime(fecha, "%Y-%m-%d")
                    .date()
                    .isoformat()
                )
            except ValueError:
                return (
                    False,
                    f"Formato de fecha inválido: {fecha}",
                )

            # Insertar gestión
            query = """
            INSERT INTO gestiones (
                ngestion, fecha, cliente, dominio, poliza, tipo, motivo,
                ncaso, usuariocarga, usuariorespuesta, estado, itr,
                totalfactura, terminado,  obs, activa
            ) VALUES (
                :ngestion, :fecha, :cliente, :dominio, :poliza, :tipo, :motivo,
                :ncaso, :usuariocarga, :usuariorespuesta, :estado, :itr,
                :totalfactura, :terminado,  :obs, :activa
            )
            """

            self.cursor.execute(
                query,
                {
                    "ngestion": ngestion,
                    "fecha": fecha_formateada,
                    "cliente": cliente,
                    "dominio": dominio,
                    "poliza": poliza,
                    "tipo": tipo,
                    "motivo": motivo,
                    "ncaso": ncaso,
                    "usuariocarga": usuariocarga,
                    "usuariorespuesta": usuariorespuesta,
                    "estado": estado,
                    "itr": itr,
                    "totalfactura": float(totalfactura),
                    "terminado": terminado,
                    "obs": obs,
                    "activa": activa,
                },
            )

            self.conn.commit()
            return True, "Gestión creada correctamente"

        except Exception as e:
            print(f"Error creando gestión: {e}")
            return False, f"Error: {str(e)}"

    def actualizar_gestion(
        self,
        gestion_id: int,
        ngestion: int,
        fecha: str,
        cliente: str,
        dominio: str,
        poliza: str,
        tipo: str,
        motivo: str,
        ncaso: int,
        usuariocarga: str,
        usuariorespuesta: str,
        estado: int,
        itr: int,
        totalfactura: float,
        terminado: int,
        obs: str,
        activa: int,
    ) -> tuple[bool, str]:
        """
        Actualiza una gestión existente en la base de datos.

        Returns:
            tuple[bool, str]: (éxito, mensaje descriptivo)
        """
        try:
            # Validar campos requeridos
            if not poliza:
                return False, "La póliza es obligatoria"

            if not tipo:
                return False, "El tipo es obligatorio"

            # Validar y formatear fecha
            try:
                fecha_formateada = (
                    datetime.datetime.strptime(fecha, "%Y-%m-%d")
                    .date()
                    .isoformat()
                )
            except ValueError:
                return (
                    False,
                    f"Formato de fecha inválido: {fecha}",
                )

            # Actualizar gestión
            query = """
            UPDATE gestiones SET
                ngestion = :ngestion,
                fecha = :fecha,
                cliente = :cliente,
                dominio = :dominio,
                poliza = :poliza,
                tipo = :tipo,
                motivo = :motivo,
                ncaso = :ncaso,
                usuariocarga = :usuariocarga,
                usuariorespuesta = :usuariorespuesta,
                estado = :estado,
                itr = :itr,
                totalfactura = :totalfactura,
                terminado = :terminado,
                obs = :obs,
                activa = :activa
            WHERE id = :gestion_id
            """

            self.cursor.execute(
                query,
                {
                    "gestion_id": gestion_id,
                    "ngestion": ngestion,
                    "fecha": fecha_formateada,
                    "cliente": cliente,
                    "dominio": dominio,
                    "poliza": poliza,
                    "tipo": tipo,
                    "motivo": motivo,
                    "ncaso": ncaso,
                    "usuariocarga": usuariocarga,
                    "usuariorespuesta": usuariorespuesta,
                    "estado": estado,
                    "itr": itr,
                    "totalfactura": float(totalfactura),
                    "terminado": terminado,
                    "obs": obs,
                    "activa": activa,
                },
            )

            self.conn.commit()
            return True, "Gestión actualizada correctamente"

        except Exception as e:
            print(f"Error actualizando gestión: {e}")
            return False, f"Error: {str(e)}"

    def eliminar_gestion(self, gestion_id: int) -> bool:
        """Elimina una gestión de la base de datos"""
        try:
            self.cursor.execute(
                "DELETE FROM gestiones WHERE id = :gestion_id",
                {"gestion_id": gestion_id},
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error eliminando gestión: {e}")
            return False

    # ========== MÉTODOS PARA FACTURAS (PERÍODOS) ==========

    def obtener_facturas(self) -> list[dict]:
        """Obtiene todas las facturas/períodos con información de notas"""
        try:
            query = """
                SELECT
                    f.id,
                    f.periodo,
                    f.importe AS importefactura,
                    COUNT(p.id) AS cantnotas,
                    COALESCE(SUM(p.importe), 0) AS importenotas
                FROM
                    facturas f
                LEFT JOIN notas n ON
                    f.id = n.factura_id
                LEFT JOIN pagos p ON
                    n.pago_id = p.id
                GROUP BY
                    f.id,
                    f.periodo,
                    f.importe
                ORDER BY
                    f.periodo DESC
            """
            result = self.cursor.execute(query).fetchall()
            return [dict(row) for row in result]
        except Exception as e:
            print(f"Error obteniendo facturas: {e}")
            return []

    def obtener_factura_por_id(self, factura_id: int) -> dict:
        """Obtiene una factura específica por su ID"""
        try:
            query = """
                SELECT 
                    id,
                    fechaemitida,
                    periodo,
                    importe
                FROM facturas
                WHERE id = :factura_id
            """
            result = self.cursor.execute(
                query, {"factura_id": factura_id}
            ).fetchone()
            return dict(result) if result else {}
        except Exception as e:
            print(f"Error obteniendo factura: {e}")
            return {}

    def crear_factura(
        self,
        periodo: int,
        fechaemitida: str,
        importe: float,
    ) -> tuple[bool, str]:
        """
        Crea una nueva factura/período en la base de datos.

        Args:
            periodo: Número del período (debe ser único)
            fechaemitida: Fecha de emisión en formato YYYY-MM-DD
            importe: Importe de la factura

        Returns:
            tuple[bool, str]: (éxito, mensaje descriptivo)
        """
        try:
            # Validar campos requeridos
            if not periodo:
                return False, "El período es obligatorio"

            # Validar y formatear fecha
            try:
                fecha_formateada = (
                    datetime.datetime.strptime(
                        fechaemitida, "%Y-%m-%d"
                    )
                    .date()
                    .isoformat()
                )
            except ValueError:
                return (
                    False,
                    f"Formato de fecha inválido: {fechaemitida}",
                )

            # Verificar que el período no exista
            existe = self.cursor.execute(
                "SELECT id FROM facturas WHERE periodo = :periodo",
                {"periodo": periodo},
            ).fetchone()

            if existe:
                return (
                    False,
                    f"Ya existe una factura para el período {periodo}",
                )

            # Insertar factura
            query = """
            INSERT INTO facturas (periodo, fechaemitida, importe)
            VALUES (:periodo, :fechaemitida, :importe)
            """

            self.cursor.execute(
                query,
                {
                    "periodo": periodo,
                    "fechaemitida": fecha_formateada,
                    "importe": float(importe) if importe else 0.0,
                },
            )

            self.conn.commit()
            return True, "Factura creada correctamente"

        except Exception as e:
            print(f"Error creando factura: {e}")
            return False, f"Error: {str(e)}"

    def actualizar_factura(
        self,
        factura_id: int,
        periodo: int,
        fechaemitida: str,
        importe: float,
    ) -> tuple[bool, str]:
        """
        Actualiza una factura existente en la base de datos.

        Args:
            factura_id: ID de la factura a actualizar
            periodo: Número del período (debe ser único)
            fechaemitida: Fecha de emisión en formato YYYY-MM-DD
            importe: Importe de la factura

        Returns:
            tuple[bool, str]: (éxito, mensaje descriptivo)
        """
        try:
            # Validar campos requeridos
            if not periodo:
                return False, "El período es obligatorio"

            # Validar y formatear fecha
            try:
                fecha_formateada = (
                    datetime.datetime.strptime(
                        fechaemitida, "%Y-%m-%d"
                    )
                    .date()
                    .isoformat()
                )
            except ValueError:
                return (
                    False,
                    f"Formato de fecha inválido: {fechaemitida}",
                )

            # Verificar que el período no exista en otra factura
            existe = self.cursor.execute(
                "SELECT id FROM facturas WHERE periodo = :periodo AND id != :factura_id",
                {"periodo": periodo, "factura_id": factura_id},
            ).fetchone()

            if existe:
                return (
                    False,
                    f"Ya existe otra factura para el período {periodo}",
                )

            # Actualizar factura
            query = """
            UPDATE facturas SET
                periodo = :periodo,
                fechaemitida = :fechaemitida,
                importe = :importe
            WHERE id = :factura_id
            """

            self.cursor.execute(
                query,
                {
                    "factura_id": factura_id,
                    "periodo": periodo,
                    "fechaemitida": fecha_formateada,
                    "importe": float(importe) if importe else 0.0,
                },
            )

            self.conn.commit()
            return True, "Factura actualizada correctamente"

        except Exception as e:
            print(f"Error actualizando factura: {e}")
            return False, f"Error: {str(e)}"

    def eliminar_factura(
        self, factura_id: int
    ) -> tuple[bool, str]:
        """
        Elimina una factura de la base de datos.

        Args:
            factura_id: ID de la factura a eliminar

        Returns:
            tuple[bool, str]: (éxito, mensaje descriptivo)
        """
        try:
            # Verificar si hay notas de crédito asociadas
            notas = self.cursor.execute(
                "SELECT COUNT(*) FROM notas WHERE factura_id = :factura_id",
                {"factura_id": factura_id},
            ).fetchone()[0]

            if notas > 0:
                return (
                    False,
                    f"No se puede eliminar la factura porque tiene {notas} nota(s) de crédito asociada(s)",
                )

            self.cursor.execute(
                "DELETE FROM facturas WHERE id = :factura_id",
                {"factura_id": factura_id},
            )
            self.conn.commit()
            return True, "Factura eliminada correctamente"
        except Exception as e:
            print(f"Error eliminando factura: {e}")
            return False, f"Error: {str(e)}"

    def obtener_notas_sin_factura(self) -> list[dict]:
        """Obtiene todas las notas de crédito que no están asociadas a ninguna factura"""
        try:
            query = """
                SELECT
                    n.id,
                    g.ngestion,
                    g.dominio,
                    g.poliza,
                    g.cliente,
                    p.fecha,
                    p.importe
                FROM
                    notas n
                JOIN pagos p ON
                    n.pago_id = p.id
                JOIN gestiones g ON
                    p.gestion_id = g.id
                WHERE
                    n.factura_id IS NULL
                ORDER BY
                    p.fecha DESC
            """
            result = self.cursor.execute(query).fetchall()
            return [dict(row) for row in result]
        except Exception as e:
            print(f"Error obteniendo notas sin factura: {e}")
            return []

    def asignar_notas_a_factura(
        self, nota_ids: list[int], factura_id: int
    ) -> tuple[bool, str]:
        """Asigna una lista de notas a una factura específica"""
        try:
            if not nota_ids:
                return False, "No hay notas para asignar"

            # Verificar que la factura existe
            factura = self.cursor.execute(
                "SELECT id FROM facturas WHERE id = :factura_id",
                {"factura_id": factura_id},
            ).fetchone()

            if not factura:
                return False, "La factura no existe"

            # Asignar cada nota a la factura
            for nota_id in nota_ids:
                self.cursor.execute(
                    "UPDATE notas SET factura_id = :factura_id WHERE id = :nota_id",
                    {
                        "factura_id": factura_id,
                        "nota_id": nota_id,
                    },
                )

            self.conn.commit()
            return (
                True,
                f"{len(nota_ids)} nota(s) asignada(s) correctamente",
            )
        except Exception as e:
            print(f"Error asignando notas a factura: {e}")
            self.conn.rollback()
            return False, f"Error: {str(e)}"

    def crear_factura_con_notas(
        self,
        periodo: int,
        fechaemitida: str,
        importe: float,
        nota_ids: list[int],
    ) -> tuple[bool, str]:
        """Crea una nueva factura y le asigna las notas especificadas"""
        try:
            # Primero crear la factura
            exito, mensaje = self.crear_factura(
                periodo, fechaemitida, importe
            )

            if not exito:
                return False, mensaje

            # Obtener el ID de la factura recién creada
            factura_id = self.cursor.lastrowid

            # Asignar las notas a la nueva factura
            if nota_ids:
                exito_asignacion, mensaje_asignacion = (
                    self.asignar_notas_a_factura(
                        nota_ids, factura_id
                    )
                )
                if not exito_asignacion:
                    return False, mensaje_asignacion

            return (
                True,
                f"Factura creada y {len(nota_ids)} nota(s) asignada(s)",
            )
        except Exception as e:
            print(f"Error creando factura con notas: {e}")
            self.conn.rollback()
            return False, f"Error: {str(e)}"

    def obtener_notas_de_factura(
        self, factura_id: int
    ) -> list[dict]:
        """Obtiene todas las notas asociadas a una factura específica"""
        try:
            query = """
                SELECT
                    n.id,
                    g.ngestion,
                    g.dominio,
                    g.poliza,
                    g.cliente,
                    p.fecha,
                    p.importe
                FROM
                    notas n
                JOIN pagos p ON
                    n.pago_id = p.id
                JOIN gestiones g ON
                    p.gestion_id = g.id
                WHERE
                    n.factura_id = :factura_id
                ORDER BY
                    p.fecha DESC
            """
            result = self.cursor.execute(
                query, {"factura_id": factura_id}
            ).fetchall()
            return [dict(row) for row in result]
        except Exception as e:
            print(f"Error obteniendo notas de factura: {e}")
            return []

    def desasociar_nota_de_factura(
        self, nota_id: int
    ) -> tuple[bool, str]:
        """Desasocia una nota de su factura (establece factura_id a NULL)"""
        try:
            self.cursor.execute(
                "UPDATE notas SET factura_id = NULL WHERE id = :nota_id",
                {"nota_id": nota_id},
            )
            self.conn.commit()
            return True, "Nota desasociada correctamente"
        except Exception as e:
            print(f"Error desasociando nota: {e}")
            self.conn.rollback()
            return False, f"Error: {str(e)}"

    # --- DOCUMENTOS ---

    def obtener_documentos_por_gestion(
        self, gestion_id: int
    ) -> list[dict]:
        """Obtiene todos los documentos asociados a una gestión"""
        try:
            query = """
                SELECT 
                    d.id,
                    d.titulo,
                    d.descripcion,
                    d.nombre_archivo,
                    d.mime_type,
                    d.tamano,
                    d.creado_en
                FROM documentos d
                INNER JOIN gestion_documento gd ON d.id = gd.documento_id
                WHERE gd.gestion_id = :gestion_id
                ORDER BY d.creado_en DESC
            """
            result = self.cursor.execute(
                query, {"gestion_id": gestion_id}
            ).fetchall()
            return [dict(row) for row in result]
        except Exception as e:
            print(f"Error obteniendo documentos: {e}")
            return []

    def crear_documento(
        self,
        gestion_id: int,
        titulo: str,
        nombre_archivo: str,
        ruta: str,
        hash: str,
        tamano: int,
        descripcion: str = None,
        mime_type: str = None,
        creado_por: str = None,
    ) -> tuple[bool, str]:
        """Crea un documento y lo asocia a una gestión"""
        try:
            # Verificar si ya existe un documento con ese hash
            existe = self.cursor.execute(
                "SELECT id FROM documentos WHERE hash = :hash",
                {"hash": hash},
            ).fetchone()

            if existe:
                # El archivo ya existe, solo asociarlo a la gestión
                documento_id = existe["id"]
                # Verificar si ya está asociado
                ya_asociado = self.cursor.execute(
                    """SELECT 1 FROM gestion_documento 
                       WHERE gestion_id = :gestion_id AND documento_id = :documento_id""",
                    {
                        "gestion_id": gestion_id,
                        "documento_id": documento_id,
                    },
                ).fetchone()

                if ya_asociado:
                    return (
                        False,
                        "Este documento ya está asociado a la gestión",
                    )

                # Asociar documento existente a la gestión
                self.cursor.execute(
                    """INSERT INTO gestion_documento (gestion_id, documento_id)
                       VALUES (:gestion_id, :documento_id)""",
                    {
                        "gestion_id": gestion_id,
                        "documento_id": documento_id,
                    },
                )
                self.conn.commit()
                return (
                    True,
                    "Documento asociado correctamente (archivo ya existía)",
                )

            # Crear nuevo documento
            self.cursor.execute(
                """INSERT INTO documentos 
                   (titulo, descripcion, nombre_archivo, mime_type, tamano, hash, ruta, creado_por)
                   VALUES (:titulo, :descripcion, :nombre_archivo, :mime_type, :tamano, :hash, :ruta, :creado_por)""",
                {
                    "titulo": titulo,
                    "descripcion": descripcion,
                    "nombre_archivo": nombre_archivo,
                    "mime_type": mime_type,
                    "tamano": tamano,
                    "hash": hash,
                    "ruta": ruta,
                    "creado_por": creado_por,
                },
            )
            documento_id = self.cursor.lastrowid

            # Asociar a la gestión
            self.cursor.execute(
                """INSERT INTO gestion_documento (gestion_id, documento_id)
                   VALUES (:gestion_id, :documento_id)""",
                {
                    "gestion_id": gestion_id,
                    "documento_id": documento_id,
                },
            )

            self.conn.commit()
            return (
                True,
                "Documento creado y asociado correctamente",
            )
        except Exception as e:
            print(f"Error creando documento: {e}")
            self.conn.rollback()
            return False, f"Error: {str(e)}"

    def desasociar_documento(
        self, gestion_id: int, documento_id: int
    ) -> tuple[bool, str]:
        """Desasocia un documento de una gestión"""
        try:
            self.cursor.execute(
                """DELETE FROM gestion_documento 
                   WHERE gestion_id = :gestion_id AND documento_id = :documento_id""",
                {
                    "gestion_id": gestion_id,
                    "documento_id": documento_id,
                },
            )
            self.conn.commit()
            return True, "Documento desasociado correctamente"
        except Exception as e:
            print(f"Error desasociando documento: {e}")
            self.conn.rollback()
            return False, f"Error: {str(e)}"

    def obtener_ruta_documento(
        self, documento_id: int
    ) -> str | None:
        """Obtiene la ruta del archivo de un documento"""
        try:
            result = self.cursor.execute(
                "SELECT ruta, nombre_archivo FROM documentos WHERE id = :id",
                {"id": documento_id},
            ).fetchone()
            return dict(result) if result else None
        except Exception as e:
            print(f"Error obteniendo ruta documento: {e}")
            return None

    def _detectar_mime(self, nombre_archivo: str) -> str:
        """Detecta el tipo MIME basándose en la extensión"""
        import mimetypes

        mime, _ = mimetypes.guess_type(nombre_archivo)
        return mime or "application/octet-stream"

    def importar_gestiones_desde_excel(
        self, file_path: str
    ) -> tuple[bool, dict]:
        """
        Importa gestiones desde un archivo Excel.
        Actualiza las existentes e inserta las nuevas.

        Returns:
            tuple[bool, dict]: (éxito, estadísticas)
            estadísticas = {
                'actualizadas': int,
                'insertadas': int,
                'errores': list[str]
            }
        """
        try:
            import polars as pl

            # Asegurar que file_path es una cadena
            file_path_str = str(file_path)

            # Leer Excel usando fastexcel como engine
            df = pl.read_excel(
                file_path_str,
                engine="calamine",  # fastexcel usa calamine
                schema_overrides={
                    "N° Caso": pl.Int32,
                },
            )

            # Mapeo de columnas Excel → DB
            columnas_map = {
                "Fecha": "fecha",
                "N° Gestión": "ngestion",
                "Cliente": "cliente",
                "Dominio": "dominio",
                "Póliza": "poliza",
                "Tipo": "tipo",
                "Motivo": "motivo",
                "N° Caso": "ncaso",
                "Usuario Carga": "usuariocarga",
                "Usuario Respuesta": "usuariorespuesta",
                "Estado": "estado",
                "ITR": "itr",
            }

            # Renombrar columnas que existan
            rename_dict = {
                k: v
                for k, v in columnas_map.items()
                if k in df.columns
            }
            df = df.rename(rename_dict).select(
                [
                    "ngestion",
                    "fecha",
                    "cliente",
                    "dominio",
                    "poliza",
                    "tipo",
                    "motivo",
                    "ncaso",
                    "usuariocarga",
                    "usuariorespuesta",
                    "estado",
                    "itr",
                ]
            )

            # Mapeo de estados texto → número
            estados_map = {
                "RECHAZADO": 0,
                "CERRADO": 1,
                "RECLAMADO": 2,
                "ABIERTO": 3,
                "": 0,
            }

            estadisticas = {
                "actualizadas": 0,
                "insertadas": 0,
                "errores": [],
            }

            for row in df.to_dicts():
                try:
                    ngestion = int(row.get("ngestion", 0))
                    if ngestion == 0:
                        print(row)
                        continue

                    # Convertir fecha
                    fecha = row.get("fecha")
                    if fecha is None:
                        fecha_formateada = (
                            datetime.datetime.now().strftime(
                                "%Y-%m-%d"
                            )
                        )
                    elif isinstance(fecha, str):
                        # Intentar diferentes formatos
                        for fmt in [
                            "%d/%m/%Y",
                            "%Y-%m-%d",
                            "%d/%m/%y",
                        ]:
                            try:
                                fecha_formateada = (
                                    datetime.datetime.strptime(
                                        fecha, fmt
                                    ).strftime("%Y-%m-%d")
                                )
                                break
                            except ValueError:
                                continue
                        else:
                            fecha_formateada = (
                                datetime.datetime.now().strftime(
                                    "%Y-%m-%d"
                                )
                            )
                    else:
                        # Es un objeto datetime
                        fecha_formateada = fecha.strftime(
                            "%Y-%m-%d"
                        )

                    # Convertir estado texto a número
                    estado_texto = (
                        str(row.get("estado", "")).strip().upper()
                    )
                    estado = estados_map.get(estado_texto, 0)

                    # Limpiar dominio (sin espacios)
                    dominio = (
                        str(row.get("dominio", ""))
                        .replace(" ", "")
                        .upper()
                    )

                    # Verificar si existe la gestión
                    existe = self.cursor.execute(
                        "SELECT id FROM gestiones WHERE ngestion = :ngestion",
                        {"ngestion": ngestion},
                    ).fetchone()

                    params = {
                        "ngestion": ngestion,
                        "fecha": fecha_formateada,
                        "cliente": str(
                            row.get("cliente", "")
                        ).strip(),
                        "dominio": dominio,
                        "poliza": str(
                            row.get("poliza", "")
                        ).strip(),
                        "tipo": str(row.get("tipo", "VEHICULAR"))
                        .strip()
                        .upper(),
                        "motivo": str(
                            row.get("motivo", "")
                        ).strip(),
                        "ncaso": int(row.get("ncaso", 0) or 0),
                        "usuariocarga": str(
                            row.get("usuariocarga", "")
                        ).strip(),
                        "usuariorespuesta": str(
                            row.get("usuariorespuesta", "")
                        ).strip(),
                        "estado": estado,
                        "itr": int(row.get("itr", 0) or 0),
                    }

                    if existe:
                        # UPDATE
                        query = """
                        UPDATE gestiones SET
                            fecha = :fecha,
                            cliente = :cliente,
                            dominio = :dominio,
                            poliza = :poliza,
                            tipo = :tipo,
                            motivo = :motivo,
                            ncaso = :ncaso,
                            usuariocarga = :usuariocarga,
                            usuariorespuesta = :usuariorespuesta,
                            estado = :estado,
                            itr = :itr
                        WHERE ngestion = :ngestion
                        """
                        self.cursor.execute(query, params)
                        estadisticas["actualizadas"] += 1
                    else:
                        # INSERT
                        params.update(
                            {
                                "totalfactura": 0.0,
                                "terminado": 0,
                                "obs": "",
                                "activa": 1,
                            }
                        )

                        query = """
                        INSERT INTO gestiones (
                            ngestion, fecha, cliente, dominio, poliza, tipo, motivo,
                            ncaso, usuariocarga, usuariorespuesta, estado, itr,
                            totalfactura, terminado, obs, activa
                        ) VALUES (
                            :ngestion, :fecha, :cliente, :dominio, :poliza, :tipo, :motivo,
                            :ncaso, :usuariocarga, :usuariorespuesta, :estado, :itr,
                            :totalfactura, :terminado, :obs, :activa
                        )
                        """
                        self.cursor.execute(query, params)
                        estadisticas["insertadas"] += 1

                except Exception as e:
                    error_msg = f"Error en N° Gestión {ngestion}: {str(e)}"
                    print(error_msg)
                    estadisticas["errores"].append(error_msg)
                    continue

            self.conn.commit()
            return True, estadisticas

        except Exception as e:
            print(f"Error importando Excel: {e}")
            self.conn.rollback()
            return False, {
                "actualizadas": 0,
                "insertadas": 0,
                "errores": [str(e)],
            }
