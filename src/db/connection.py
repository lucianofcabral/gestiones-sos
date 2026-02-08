"""
Gestión centralizada de conexiones a la base de datos.

Proporciona una única instancia de base de datos para toda la aplicación,
optimizando el uso de recursos y facilitando la futura migración a PostgreSQL.
"""

from typing import Optional
from src.db.database import SQLiteDB


_db_instance: Optional[SQLiteDB] = None


def get_database() -> SQLiteDB:
    """
    Retorna la instancia única de base de datos (Singleton).

    Esta función centraliza el acceso a la base de datos, lo que permite:
    - Reutilizar una única conexión en toda la aplicación
    - Reducir overhead de crear/destruir conexiones
    - Facilitar la migración futura a PostgreSQL con connection pooling

    Ejemplo de uso:
        ```python
        from src.db.connection import get_database

        database = get_database()
        pagos = database.filtrar_pagos(...)
        ```

    Para migrar a PostgreSQL en el futuro, solo necesitas modificar
    esta función para retornar conexiones de un pool:
        ```python
        # Futuro con PostgreSQL
        def get_database() -> PostgresDB:
            global _pool
            if _pool is None:
                _pool = SimpleConnectionPool(...)
            return _pool.getconn()
        ```

    Returns:
        SQLiteDB: Instancia única de la base de datos
    """
    global _db_instance

    if _db_instance is None:
        _db_instance = SQLiteDB()

    return _db_instance


def reset_database():
    """
    Reinicia la instancia de base de datos.

    Útil para:
    - Testing (crear instancia limpia entre tests)
    - Reconexión después de errores
    - Cambio de configuración en runtime

    ⚠️ Usar con precaución en producción.
    """
    global _db_instance

    if _db_instance is not None:
        # Cerrar conexión existente si es posible
        if hasattr(_db_instance, "conn"):
            try:
                _db_instance.conn.close()
            except Exception:
                pass

    _db_instance = None
