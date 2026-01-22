from django.db.models.signals import pre_save,post_save
from django.db import transaction
from django.dispatch import receiver
from .models import ImagenProducto,TokenReseña,IngresoStock,LoteStock,MovimientoStock
from core.utils import resize_to_size
from users.emails import reseña_token_html

@receiver(post_save, sender=IngresoStock)
def manejar_ingreso_stock(sender, instance:IngresoStock, created, **kwargs):
    if created:
        with transaction.atomic():
            LoteStock.objects.create(
                ingreso=instance,
                cantidad_disponible=instance.cantidad,
                costo_unitario=instance.costo_unitario,
                fecha_ingreso=instance.fecha_ingreso
            )

@receiver(post_save,sender=LoteStock)
def manejar_lote_stock(sender, instance:LoteStock, created, **kwargs):
    if created:
        with transaction.atomic():
            MovimientoStock.objects.create(
                producto=instance.ingreso.producto,
                producto_color=instance.ingreso.producto_color,
                tipo=MovimientoStock.Tipo.INGRESO,
                cantidad=instance.cantidad_disponible,
                lote=instance,
            )

@receiver(post_save, sender=TokenReseña)
def notificar_token_reseña(sender, instance, created, **kwargs):
    if created:
        reseña_token_html(instance, instance.usuario.email)

@receiver(post_save, sender=ImagenProducto)
def generar_thumbnail(sender, instance, created, **kwargs):
    if created and instance.imagen:
        # Redimensionar imagen principal a 600x600
        nueva_imagen = resize_to_size(instance.imagen, (600, 600))
        if nueva_imagen:
            instance.imagen.save(f"img600_{instance.pk}.webp", nueva_imagen, save=False)

        # Redimensionar miniatura a 200x200
        mini = resize_to_size(instance.imagen, size=(200, 200))
        if mini:
            filename = f"thumb200_{instance.pk}.webp"
            instance.imagen_200.save(filename, mini, save=False)
            instance.save()
