from .models import Tienda,EventosPromociones
from products.models import Producto
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import actualizar_precio_final,resize_to_size,gen_cache_key
from django.core.cache import cache

@receiver(post_save, sender=Tienda)
def actualizar_precios(sender, instance, **kwargs):
    for producto in Producto.objects.all():
        actualizar_precio_final(producto)
        producto.save()

@receiver(post_save, sender=Tienda)
def limpiar_cache_configuracion(sender, instance, **kwargs):
    CACHE_KEY_CONFIG = gen_cache_key("configuracion_tienda")
    cache.delete(CACHE_KEY_CONFIG)
    cache.delete('modo_mantenimiento')

@receiver(post_save, sender=EventosPromociones)
def resize_imagen_evento(sender, instance, **kwargs):
    if not instance.logo:
        return

    old = instance._old_logo
    if old and instance.logo.name == old.name:
        return

    nueva = resize_to_size(instance.logo, (200, 200))
    if nueva:
        instance.logo.save(f"evento_{instance.pk}.webp", nueva, save=False)
        sender.objects.filter(pk=instance.pk).update(logo=instance.logo)