from typing import TypedDict
from products.models import Producto

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