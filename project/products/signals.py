from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Producto
from decimal import Decimal

from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

def resize_to_200x200(image_field):
    img = Image.open(image_field)
    img = img.convert('RGB')
    img = img.resize((200, 200), Image.ANTIALIAS)
    buffer = BytesIO()
    img.save(fp=buffer, format='JPEG', quality=85)
    return ContentFile(buffer.getvalue())



@receiver(pre_save, sender=Producto)
def applys_producto(sender, instance, **kwargs):
    # * Verifica si el producto tiene un descuento
    if instance.descuento > 0:
        if not instance.precio_anterior:
            instance.precio_anterior = instance.precio
        descuento_decimal = Decimal(instance.descuento) / Decimal('100')
        instance.precio = instance.precio_anterior * (1 - descuento_decimal)
    else:
        if instance.precio_anterior:
            instance.precio = instance.precio_anterior
            instance.precio_anterior = None
    # * Verifica si tiene portada
    if instance.portada and not instance.portada.name.startswith("portadas_200"):
        nueva_imagen = resize_to_200x200(instance.portada)
        instance.portada.save(f"portadas_200_{instance.pk or 'temp'}.jpg", nueva_imagen, save=False)
