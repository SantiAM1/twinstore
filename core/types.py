from typing import TypedDict, Optional, Dict, Any

class ConfigDict(TypedDict):
    id: int
    nombre_tienda: str
    modo_stock: str
    mostrar_stock_en_front: bool
    borrar_cupon: bool
    mantenimiento: bool
    divisa: str
    valor_dolar: float
    maximo_compra: int
    fecha_actualizacion_dolar: str
    fecha_actualizacion_config: str
