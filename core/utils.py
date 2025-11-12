from decimal import Decimal
from .models import DolarConfiguracion,ConfiguracionTienda
from django.core.cache import cache
from django.conf import settings

def actualizar_precio_final(producto, valor_dolar) -> None:
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

def obtener_valor_dolar() -> Decimal:
    """
    Obtiene el valor actual del dólar desde la configuración.
    """
    dolar = DolarConfiguracion.objects.first()
    return dolar.valor

CACHE_KEY_CONFIG = "configuracion_tienda"

def get_configuracion_tienda() -> ConfiguracionTienda:
    """
    Obtiene la configuración general de la tienda desde caché.
    Si no existe, la crea o la guarda automáticamente.
    """
    config = cache.get(CACHE_KEY_CONFIG)
    if config:
        return config

    config = ConfiguracionTienda.objects.first()
    if not config:
        config = ConfiguracionTienda.objects.create()

    time = 43200 if not settings.DEBUG else 5

    cache.set(CACHE_KEY_CONFIG, config, timeout=time)
    return config