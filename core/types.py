from typing import TypedDict

class ConfigDict(TypedDict):
    nombre_tienda: str
    modo_stock: str
    color_primario: str
    color_secundario: str
    mostrar_stock_en_front: bool
    borrar_cupon: bool
    mantenimiento: bool
    divisa: str
    valor_dolar: float
    maximo_compra: int
