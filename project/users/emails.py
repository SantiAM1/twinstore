from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
import threading

def enviar_mail_confirmacion_html(usuario):
    perfil = usuario.perfil
    token = perfil.token_verificacion
    site_url = f'{settings.MY_NGROK_URL}'
    context = {
        'url' : f"http://{site_url}/usuario/verificar/{token}",
        'img' : f"http://{site_url}/static/img/mail.png"
    }

    html = render_to_string('emails/bienvenida_usuario.html', context)
    text = f'Hola {usuario.email}, para verificar tu cuenta hacé clic en: https://{site_url}/verificar/{token}'

    msg = EmailMultiAlternatives(
        subject='Confirmá tu cuenta en Twinstore',
        body=text,
        from_email='Twinstore <notificaciones@twinstore.com>',
        to=[usuario.email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()

def enviar_mail_async(usuario):
    """Envía el mail de confirmación en un hilo separado para no bloquear la respuesta HTTP"""
    threading.Thread(target=enviar_mail_confirmacion_html, args=(usuario,)).start()