from django.conf import settings
from .tasks import enviar_mail_compra,enviar_mail_confirm_user,enviar_mail_estado_pedido

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

def mail_estado_pedido_html(historial,user_email):
    """Envía el mail cuando hay un cambio en el estado del pedido"""
    token = historial.token_consulta
    site_url = f'{settings.MY_NGROK_URL}'

    if historial.estado == "confirmado":
        mensaje = "Tu pago fue confirmado con éxito. ¡Gracias por tu compra! Pronto comenzaremos a preparar tu pedido."
    elif historial.estado == "rechazado":
        mensaje = "Hubo un problema con el pago. Te recomendamos volver a intentarlo o escribirnos si necesitás ayuda."
    elif historial.estado == "preparando pedido":
        mensaje = "Estamos preparando tu pedido! En breve recibiras noticias."
    elif historial.estado == "enviado":
        mensaje = "¡Tu pedido ha sido enviado! En las próximas horas te compartiremos más detalles del seguimiento."
    elif historial.estado == "finalizado":
        mensaje = "	¡Gracias por confiar en Twinstore! Tu pedido ha sido entregado y finalizado exitosamente. Esperamos volver a verte pronto."
    elif historial.estado == "arrepentido":
        mensaje = "	Pedido cancelado, arrepentido"
    else:
        mensaje = "Estamos esperando la confirmación del pago. Te notificaremos apenas se acredite."

    estado = historial.estado
    estado = estado.capitalize()

    mail_data = {
        'url': f"http://{site_url}/usuario/ver_pedido/{token}",
        'img': f"http://{site_url}/static/img/mail.webp",
        'pedido_id': historial.merchant_order_id,
        'estado': estado,
        'mensaje': mensaje
    }
    enviar_mail_estado_pedido.delay(mail_data, user_email)