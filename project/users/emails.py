from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
import threading

def mail_confirm_user_html(usuario):
    perfil = usuario.perfil
    token = perfil.token_verificacion
    site_url = f'{settings.MY_NGROK_URL}'
    context = {
        'url' : f"http://{site_url}/usuario/verificar/{token}",
        'img' : f"http://{site_url}/static/img/mail.webp"
    }

    html = render_to_string('emails/bienvenida_usuario.html', context)
    text = f'Hola {usuario.email}, para verificar tu cuenta hacé clic en: https://{site_url}/verificar/{token}'

    msg = EmailMultiAlternatives(
        subject='Confirmá tu cuenta en Twinstore',
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[usuario.email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()

def mail_confirm_user_async(usuario):
    """Envía el mail de confirmación separado para no bloquear la respuesta HTTP"""
    threading.Thread(target=mail_confirm_user_html, args=(usuario,)).start()

def mail_buy_send_html(historial,user_email):
    token = historial.token_consulta
    site_url = f'{settings.MY_NGROK_URL}'
    context = {
        'url' : f"http://{site_url}/usuario/ver_pedido/{token}",
        'img' : f"http://{site_url}/static/img/mail.webp",
        'token': token
    }

    html = render_to_string('emails/compra_exitosa.html', context)
    text = f'Gracias por tu compra! Este es tu codigo de seguimiento:{token}'

    msg = EmailMultiAlternatives(
        subject='Compra recibida - Twistore',
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()

def mail_buy_send_async(historial,user_email):
    """Envía el mail de compra exitosa separado para no bloquear la respuesta HTTP"""
    threading.Thread(target=mail_buy_send_html, args=(historial,user_email,)).start()