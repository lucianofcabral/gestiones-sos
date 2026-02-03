import sqlite3
from pathlib import Path
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
                query: str = f"Select * from {tabla} ;"
                with pyodbc.connect(conn_str) as cn:
                    cur = cn.cursor()
                    cur.execute(query)
                    rows = cur.execute(query).fetchall()
                    cols = [
                        column[0] for column in cur.description
                    ]
                    data: list[dict] = [
                        dict(zip(cols, row)) for row in rows
                    ]
                    dataframe: pl.DataFrame = pl.from_dicts(data)
                return dataframe

            facturas = get_polars_from_table("Facturas")
            tres_arr = get_polars_from_table("TresArroyos")
            formas_pago = get_polars_from_table("catFormasDePago")
            # cat_gestiones = get_polars_from_table("catEstadoGestiones")
            destinatarios = get_polars_from_table(
                "catDestinatarios"
            )
            pagadores = get_polars_from_table("catPagadores")

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
                    "nrofactura",
                    pl.col("fechaemitida").dt.strftime(
                        "%Y-%m-%d"
                    ),
                    pl.col("periodo").dt.strftime("%Y%m"),
                    pl.col("importe").cast(pl.Float32),
                ]
            )
            for row in facturas_data.to_dicts():
                self.cursor.execute(
                    "Insert into facturas (nrofactura,fechaemitida,periodo,importe) values (:nrofactura,:fechaemitida,:periodo,:importe);",
                    {
                        "nrofactura": str(row["nrofactura"]),
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

            # gESTIONES
            gestiones_concatenado = pl.concat(
                [
                    gestiones.with_columns(
                        [
                            pl.col("Fecha").dt.strftime(
                                "%Y-%m-%d"
                            ),
                            pl.col("Poliza")
                            .cast(pl.Int64)
                            .cast(pl.String),
                            pl.col("TotalFactura").cast(
                                pl.Float32
                            ),
                            pl.col("FechaTerminado").dt.strftime(
                                "%Y-%m-%d"
                            ),
                            pl.col("Activa").cast(pl.Int64),
                            pl.col("Terminado").cast(pl.Int64),
                            pl.lit(None)
                            .alias("IdGestion3A")
                            .cast(pl.Int64),
                        ]
                    ),
                    tres_arr.sort(["Fecha", "NroFactura"]).select(
                        [
                            pl.lit(0)
                            .alias("NGestion")
                            .cast(pl.Int64),
                            pl.col("Fecha").dt.strftime(
                                "%Y-%m-%d"
                            ),
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
                            pl.lit(0)
                            .alias("Estado")
                            .cast(pl.Int64),
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
                            .dt.strftime("%Y-%m-%d")
                            .alias("FechaTerminado"),
                            "Obs",
                            pl.lit(1)
                            .cast(pl.Int64)
                            .alias("Activa"),
                            pl.col("Id").alias("IdGestion3A"),
                        ]
                    ),
                ]
            )
            gestiones_concatenado = gestiones_concatenado.select(
                [
                    pl.col(col).alias(col.lower())
                    for col in gestiones_concatenado.columns
                ]
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
                            pl.col("Fecha").dt.strftime(
                                "%Y-%m-%d"
                            )
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
                        pl.col("Fecha").dt.strftime("%Y-%m-%d")
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
                        pl.col("importe").cast(pl.Float64),
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
                pl.col("FechaPasada").dt.strftime("%Y-%m-%d")
            ).sort("IdPago")
            notas_data = notas_data.select(
                [
                    pl.col(col).alias(col.lower())
                    for col in notas_data.columns
                ]
            ).with_columns(pl.col("pasada").cast(pl.Int64))

            for row in notas_data.to_dicts():
                try:
                    pagoid = 0
                    factid = None
                    pagoid = self.cursor.execute(
                        "Select id_nuevo from aux_pagos where id_viejo = :id_viejo;",
                        {"id_viejo": row["idpago"]},
                    ).fetchone()[0]
                    factid = self.cursor.execute(
                        "Select id_nuevo from aux_facturas where id_viejo = :id_viejo;",
                        {"id_viejo": row["idfactura"]},
                    ).fetchone()
                    if isinstance(factid, tuple):
                        factid = factid[0]
                    else:
                        factid = None

                    self.cursor.execute(
                        "Insert into notas (pago_id,factura_id,pasada) values (:pago_id,:factura_id,:pasada);",
                        {
                            "pago_id": pagoid,
                            "factura_id": factid,
                            "pasada": row["pasada"],
                        },
                    )
                except Exception as e:
                    print(
                        f"Error procesando nota: {row}\n {(pagoid, factid)} \n{e}"
                    )
                    continue

        self.connection.commit()

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
                                and n.pasada = 1
                        )
            )"""

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

        print("Executing query:", query)
        print("With params:", params)

        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
