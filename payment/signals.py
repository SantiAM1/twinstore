from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from .models import TicketDePago

@receiver(post_save,sender=TicketDePago)
def actualizar_venta(sender, instance:TicketDePago, created, **kwargs):
    if instance.estado == "aprobado":
        instance.venta.check_venta()
