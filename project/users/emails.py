from django.conf import settings
from .tasks import enviar_mail_compra,enviar_mail_confirm_user

def mail_confirm_user_html(usuario):
    """Envía el mail de confirmación de cuenta"""
    perfil = usuario.perfil
    token = perfil.token_verificacion
    site_url = f'{settings.MY_NGROK_URL}'
    mail_data = {
        'url' : f"http://{site_url}/usuario/verificar/{token}",
        'img' : f"http://{site_url}/static/img/mail.webp"
    }

    enviar_mail_confirm_user.delay(mail_data,user_email=usuario.email)

def mail_buy_send_html(historial,user_email):
    """Envía el mail de compra exitosa"""
    token = historial.token_consulta
    site_url = f'{settings.MY_NGROK_URL}'
    historial_data = {
    'url': f"http://{site_url}/usuario/ver_pedido/{token}",
    'img': f"http://{site_url}/static/img/mail.webp",
    'token': token,
    }
    enviar_mail_compra.delay(historial_data, user_email)