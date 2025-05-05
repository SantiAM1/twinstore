from decimal import Decimal
from .models import DolarConfiguracion

def actualizar_precio_final(producto, valor_dolar):
    """
    Calcula el precio final en ARS a partir del precio en USD y el descuento.
    """
    if producto.precio_dolar is None:
        return 

    precio_base = round(producto.precio_dolar * valor_dolar, 2)

    if producto.descuento > 0:
        descuento_decimal = Decimal(producto.descuento) / Decimal('100')
        producto.precio = round(precio_base * (1 - descuento_decimal), 2)
    else:
        producto.precio = precio_base

def obtener_valor_dolar():
    dolar = DolarConfiguracion.objects.first()
    return dolar.valor