from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario,DatosFacturacion,TokenUsers
from .emails import mail_buy_send_html,mail_confirm_user_html

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
    mail_buy_send_html(instance.venta,instance.email)

@receiver(post_save, sender=TokenUsers)
def enviar_mail_token(sender, instance:TokenUsers, created, **kwargs):
    if created:
        if instance.tipo == 'verificar':
            mail_confirm_user_html(instance.user)
        elif instance.tipo == 'recuperar':
            # * Agregar la función para enviar el correo de recuperación
            pass