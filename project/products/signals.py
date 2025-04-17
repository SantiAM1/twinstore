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
    # * Aplicar descuento al precio si existe
    if instance.descuento > 0:
        if instance.precio_anterior is None:
            instance.precio_anterior = instance.precio
        descuento_decimal = Decimal(instance.descuento) / Decimal('100')
        instance.precio = instance.precio_anterior * (1 - descuento_decimal)
    else:
        if instance.precio_anterior is not None:
            instance.precio = instance.precio_anterior
            instance.precio_anterior = None

    # * Redimensionar portada si fue modificada
    if instance.pk:
        try:
            old = Producto.objects.get(pk=instance.pk)
            portada_cambiada = instance.portada != old.portada
        except Producto.DoesNotExist:
            portada_cambiada = True
    else:
        portada_cambiada = True

    if instance.portada and portada_cambiada:
        nueva_imagen = resize_to_size(instance.portada, size=(200, 200))
        if nueva_imagen:
            instance.portada.save(f"portadas_200_{instance.pk or 'temp'}.webp", nueva_imagen, save=False)

@receiver(post_save, sender=ImagenProducto)
def generar_thumbnail(sender, instance, created, **kwargs):
    if created and instance.imagen:
        # Redimensionar imagen principal a 600x600
        nueva_imagen = resize_to_size(instance.imagen, (600, 600))
        if nueva_imagen:
            instance.imagen.save(f"img600_{instance.pk}.webp", nueva_imagen, save=False)

        # Redimensionar miniatura a 100x100
        mini = resize_to_size(instance.imagen, size=(100, 100))
        if mini:
            filename = f"thumb100_{instance.pk}.webp"
            instance.imagen_100.save(filename, mini, save=False)
            instance.save()
