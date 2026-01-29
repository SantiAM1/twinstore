from shipping.models import ShippingConfig
from shipping.services.zipnova import ZipnovaService
from core.models import Tienda
from products.models import Producto
from decimal import Decimal
from cart.types import CarritoDict

CARRITO:list[CarritoDict] = [
    {
        'id': 36,
        'sku': 'LOG-GEN-9261-A8B4',
        'producto_id': 1,
        'nombre': 'Producto 1',
        'variante': 'Color: Rojo | Talle: S',
        'imagen': '/media/productos/imagenes/thumb200_1.webp',
        'url_producto': '/productos/producto-1/',
        'cantidad': 2,
        'precio': Decimal('2112000.00'),
        'tiene_descuento': True,
        'precio_anterior': Decimal('2400000.00'),
        'ahorro': Decimal('288000.00')
    },
    {
        'id': 37,
        'sku': 'LOG-GEN-9075-E2CE',
        'producto_id': 2,
        'nombre': 'Producto 2',
        'variante': 'Talle: M | Rebatible: SI',
        'imagen': '/media/productos/imagenes/thumb200_7.webp',
        'url_producto': '/productos/producto-2/',
        'cantidad': 2,
        'precio': Decimal('360.00'),
        'tiene_descuento': True,
        'precio_anterior': Decimal('400.00'),
        'ahorro': Decimal('40.00')
        }
    ]

def run():
    shipping_config = ShippingConfig.objects.first()
    if not shipping_config:
        print(f"❌ La tienda no tiene configurado ShippingConfig.")
        return
    
    service = ZipnovaService(shipping_config)

    carrito = CARRITO
    resultado = service.cotizar(carrito,cuidad="Palermo",estado="Capital federal",codigo_postal="1425")