from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import TicketDePago

@shared_task
def eliminar_tickets_expirados():
    """
    Cancela o elimina tickets expirados (más de 30 minutos).
    """
    limite = timezone.now() - timedelta(minutes=30)
    expirados = TicketDePago.objects.filter(
        creado__lt=limite
    ).exclude(estado='aprobado')

    total = 0
    for ticket in expirados:
        ticket.cancelar_ticket()
        total += 1

    return f"{total} tickets expirados eliminados."
