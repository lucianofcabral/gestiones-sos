"""Estado global de la aplicación"""


class FiltrosStateGestiones:
    """Estado de los filtros de gestiones"""

    def __init__(self):
        self.texto_busqueda: str = ""
        self.tipo: str = "all"
        self.terminado: bool = False
        self.no_terminado: bool = False
        self.activa: bool = True
        self.no_activa: bool = False
        self.con_pagos: bool = False
        self.sin_pagos: bool = False
        self.con_nota: bool = False
        self.sin_nota: bool = False
        self.con_nota_pasada: bool = False

        self.gestiones_seleccionados: list = []


# Instancia global de filtros
filtros_gestiones = FiltrosStateGestiones()


class FiltrosStatePagos:
    """Estado de los filtros de pagos"""

    def __init__(self):
        self.texto_busqueda: str = ""
        self.pagador: str = ""
        self.destinatario: str = ""
        self.formapago: str = ""
        self.es_nota_credito_no_pasada: bool = False


filtros_pagos = FiltrosStatePagos()
