from celery import shared_task
from .models import Producto
from core.models import EventosPromociones

@shared_task
def evento_finalizado():
    """
    Desasigna el evento de los productos si el evento ha finalizado.
    """
    evento = EventosPromociones.objects.first()
    if not evento.esta_activo:
        productos = Producto.objects.filter(evento=evento)
        for producto in productos:
            producto.evento = None
            producto.precio_evento = None
            producto.save()
    
    evento.delete()
