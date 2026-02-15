"""Componente reutilizable para el select de estado con creación automática"""

from nicegui import ui
from src.db.connection import get_database


def crear_estado_select(
    value=None,
    label="Estado",
    dense=False,
    on_change=None,
    **kwargs,
):
    """
    Crea un select para estados que permite escribir nuevos valores y los mantiene.
    El estado se creará automáticamente en la BD al guardar la gestión.

    Args:
        value: Valor inicial
        label: Etiqueta del campo
        dense: Si debe ser compacto
        on_change: Callback cuando cambia el valor
        **kwargs: Argumentos adicionales para el select

    Returns:
        ui.select: El componente select configurado
    """
    database = get_database()

    # Obtener estados existentes
    estados_existentes = database.obtener_estados() or [
        "Pendiente",
        "En Proceso",
        "Finalizado",
    ]

    # Asegurar que el valor inicial esté en las opciones si existe
    if value and value not in estados_existentes:
        estados_existentes.append(value)

    # Si el valor es un string vacío, usar None
    valor_inicial = value if value else None

    # Crear el select con new-value-mode para permitir agregar valores
    select = ui.select(
        options=estados_existentes,
        value=valor_inicial,
        label=label,
        with_input=True,
        on_change=on_change,
        **kwargs,
    )

    # Permitir agregar nuevos valores únicos
    select.props('new-value-mode="add-unique"')

    if dense:
        select.props("dense")
    else:
        select.props("filled")

    return select
