from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario,DatosFacturacion
from .emails import mail_buy_send_html
from django.conf import settings

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    if hasattr(instance, 'perfil'):
        instance.perfil.save()

@receiver(post_save, sender=DatosFacturacion)
def enviar_mail_compra(sender, instance, **kwargs):
    if getattr(settings, "DEBUG", True):
        return
    mail_buy_send_html(instance.historial,instance.email)