from core.models import EventosPromociones
from products.models import Producto

def run():
    evento = EventosPromociones.objects.first()
    if not evento.esta_activo:
        productos = Producto.objects.filter(evento=evento)
        for producto in productos:
            producto.evento = None
            producto.precio_evento = None
            producto.save()