from typing import TypedDict

class CarritoDict(TypedDict):
    id: int
    sku: str
    producto_id: int
    nombre: str
    variante: str | None
    imagen: str
    url_producto: str
    cantidad: int
    precio: float
    tiene_descuento: bool
    precio_anterior: float
    ahorro: float