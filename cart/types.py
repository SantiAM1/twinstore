from typing import TypedDict
from products.models import Producto

class CarritoDict(TypedDict):
    id: int
    producto_id: int
    producto: Producto
    color_id: int | None
    cantidad: int
    precio: float
    nombre: str
    imagen: str
    precio_anterior: float | None
    descuento: float | None