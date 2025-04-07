# products/signals.py

from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Producto
from decimal import Decimal

@receiver(pre_save, sender=Producto)
def aplicar_descuento(sender, instance, **kwargs):
    if instance.descuento > 0:
        if not instance.precio_anterior:
            instance.precio_anterior = instance.precio

        descuento_decimal = Decimal(instance.descuento) / Decimal('100')
        instance.precio = instance.precio_anterior * (1 - descuento_decimal)

    else:
        if instance.precio_anterior:
            instance.precio = instance.precio_anterior
            instance.precio_anterior = None