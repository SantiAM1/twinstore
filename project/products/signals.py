from django.db.models.signals import pre_save,post_save
from django.dispatch import receiver
from .models import Producto, ImagenProducto
from decimal import Decimal

from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE = Image.ANTIALIAS

import os

def resize_to_size(image_field, size=(200, 200)):
    if not image_field:
        return None
    try:
        img = Image.open(image_field)
        img = img.convert('RGB')
        img.thumbnail(size, RESAMPLE)
        buffer = BytesIO()
        img.save(fp=buffer, format='WEBP', quality=85)
        return ContentFile(buffer.getvalue())
    except Exception as e:
        print(f"[ERROR al redimensionar portada]: {e}")
        return None


@receiver(pre_save, sender=Producto)
def applys_producto(sender, instance, **kwargs):
    # * Aplica descuento si hay
    if instance.descuento > 0:
        if not instance.precio_anterior:
            instance.precio_anterior = instance.precio
        descuento_decimal = Decimal(instance.descuento) / Decimal('100')
        instance.precio = instance.precio_anterior * (1 - descuento_decimal)
    else:
        if instance.precio_anterior:
            instance.precio = instance.precio_anterior
            instance.precio_anterior = None

    # * Redimensionar portada si no fue procesada aún
    if instance.portada and not instance.portada.name.startswith("portadas_200"):
        nueva_imagen = resize_to_size(instance.portada,size=(200, 200))
        if nueva_imagen:
            instance.portada.save(f"portadas_200_{instance.pk or 'temp'}.webp", nueva_imagen, save=False)

@receiver(post_save, sender=ImagenProducto)
def generar_thumbnail(sender, instance, created, **kwargs):
    if created and instance.imagen:
        original_path = instance.imagen.path
        # * Redimensionar imagen a 600x600
        nueva_imagen = resize_to_size(instance.imagen, (600, 600))
        if nueva_imagen:
            instance.imagen.save(f"img600_{instance.pk}.webp", nueva_imagen, save=False)

        # * Borrar archivo original si aún existe
        if os.path.exists(original_path):
            os.remove(original_path)

        # * 👉 Si ya había miniatura, eliminarla
        if instance.imagen_100 and os.path.isfile(instance.imagen_100.path):
            os.remove(instance.imagen_100.path)

        # * Redimensionar imagen a 100x100
        mini = resize_to_size(instance.imagen, size=(100, 100))
        if mini:
            filename = f"thumb100_{instance.pk}.webp"
            instance.imagen_100.save(filename, mini, save=False)
            instance.save()