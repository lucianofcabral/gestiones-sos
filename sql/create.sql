-- agentes definition
CREATE TABLE IF NOT EXISTS agentes (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    agente TEXT NOT NULL,
    UNIQUE (agente)
);
--
CREATE TABLE IF NOT EXISTS aux_agentes (
    id_destinatario integer,
    id_pagador integer,
    id_nuevo integer
);

-- formaspago definition
CREATE TABLE IF NOT EXISTS formaspago (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    formapago TEXT NOT NULL,
    UNIQUE (formapago)
);
--
CREATE TABLE IF NOT EXISTS aux_formaspago (
    id_viejo integer,
    id_nuevo integer
);

-- facturas
CREATE TABLE IF NOT EXISTS facturas (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    fechaemitida DATE,
    periodo INTEGER NOT NULL,
    importe REAL DEFAULT(0.0),
    UNIQUE (periodo)
);
--
CREATE TABLE IF NOT EXISTS aux_facturas (
    id_viejo integer,
    id_nuevo integer
);
-- gestiones definition
CREATE TABLE IF NOT EXISTS gestiones (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    ngestion INTEGER DEFAULT(0) NOT NULL,
    fecha DATE,
    cliente TEXT,
    dominio TEXT,
    poliza TEXT NOT NULL,
    tipo TEXT NOT NULL,
    motivo TEXT,
    ncaso INTEGER DEFAULT(0) NOT NULL,
    usuariocarga TEXT,
    usuariorespuesta TEXT,
    estado INTEGER DEFAULT(0) NOT NULL,
    itr INTEGER DEFAULT(0) NOT NULL,
    totalfactura REAL DEFAULT(0.0) NOT NULL,
    terminado INTEGER DEFAULT(0) NOT NULL,
    obs TEXT,
    activa INTEGER DEFAULT(0) NOT NULL
);
--
CREATE TABLE IF NOT EXISTS aux_gestiones (
    ngestion integer,
    id_viejo integer,
    id_nuevo integer
);

-- pagos
CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    gestion_id INTEGER NOT NULL,
    fecha DATE NOT NULL,
    pagador_id INTEGER NOT NULL,
    destinatario_id INTEGER NOT NULL,
    formapago_id INTEGER NOT NULL,
    importe REAL NOT NULL CHECK (importe > 0),
    FOREIGN KEY (gestion_id) REFERENCES gestiones (id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (pagador_id) REFERENCES agentes (id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (destinatario_id) REFERENCES agentes (id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (formapago_id) REFERENCES formaspago (id) ON DELETE CASCADE ON UPDATE CASCADE
);
--
CREATE TABLE IF NOT EXISTS aux_pagos (
    id_viejo integer,
    id_nuevo integer
);

-- notas
CREATE TABLE IF NOT EXISTS notas (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    pago_id INTEGER NOT NULL,
    factura_id INTEGER NULL,
    FOREIGN KEY (pago_id) REFERENCES pagos (id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (factura_id) REFERENCES facturas (id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE (pago_id)
);

-- TRIGGER gestiones
CREATE TRIGGER validar_ngestion
BEFORE INSERT ON gestiones
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'El valor de ngestion ya existe en la tabla')
    WHERE NEW.ngestion != 0 
    AND EXISTS (
        SELECT 1 FROM gestiones 
        WHERE ngestion = NEW.ngestion
    );
END;

-- documentos
CREATE TABLE IF NOT EXISTS documentos (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    nombre_archivo TEXT NOT NULL,
    mime_type TEXT,
    tamano INTEGER NOT NULL,
    hash TEXT NOT NULL,
    ruta TEXT NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    creado_por TEXT,
    UNIQUE (hash)
);

-- gestion_documento (many-to-many)
CREATE TABLE IF NOT EXISTS gestion_documento (
    gestion_id INTEGER NOT NULL,
    documento_id INTEGER NOT NULL,
    PRIMARY KEY (gestion_id, documento_id),
    FOREIGN KEY (gestion_id) REFERENCES gestiones (id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (documento_id) REFERENCES documentos (id) ON DELETE CASCADE ON UPDATE CASCADE
);