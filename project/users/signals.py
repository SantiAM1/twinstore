from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario,DatosFacturacion
from .emails import mail_buy_send_async

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    # Guarda automáticamente el perfil si el usuario se actualiza
    if hasattr(instance, 'perfil'):
        instance.perfil.save()

@receiver(post_save, sender=DatosFacturacion)
def enviar_mail_compra(sender, instance, **kwargs):
    mail_buy_send_async(instance.historial,instance.email)