from typing import TypedDict, Optional, Dict, Any

class ConfigDict(TypedDict):
    nombre_tienda: str
    modo_stock: str
    mostrar_stock_en_front: bool
    borrar_cupon: bool
    mantenimiento: bool
    divisa: str
    valor_dolar: float
    maximo_compra: int
