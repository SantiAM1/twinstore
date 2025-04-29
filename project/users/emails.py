from django.conf import settings
from .tasks import enviar_mail_compra,enviar_mail_confirm_user,enviar_mail_estado_pedido,enviar_mail_comprobante_obs

def mail_confirm_user_html(usuario):
    """Envía el mail de confirmación de cuenta"""
    perfil = usuario.perfil
    token = perfil.token_verificacion
    site_url = f'{settings.SITE_URL}'
    mail_data = {
        'url' : f"{site_url}/usuario/verificar/{token}",
        'img' : f"{site_url}/static/img/mail.webp"
    }
    enviar_mail_confirm_user.delay(mail_data,user_email=usuario.email)

def mail_buy_send_html(historial,user_email):
    """Envía el mail de compra exitosa"""
    token = historial.token_consulta
    site_url = f'{settings.SITE_URL}'
    productos = historial.productos
    adicional = historial.get_adicional()
    total = historial.total_compra
    historial_data = {
    'url': f"{site_url}/usuario/ver_pedido/{token}",
    'img': f"{site_url}/static/img/mail.webp",
    'token': token,
    'productos':productos,
    'adicional':adicional,
    'total':total
    }
    enviar_mail_compra.delay(historial_data, user_email)

def mail_estado_pedido_html(historial,user_email):
    """Envía el mail cuando hay un cambio en el estado del pedido"""
    token = historial.token_consulta
    site_url = f'{settings.SITE_URL}'

    finalizado = False
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
        finalizado = True
    elif historial.estado == "arrepentido":
        mensaje = "	Pedido cancelado, arrepentido"
    else:
        mensaje = "Estamos esperando la confirmación del pago. Te notificaremos apenas se acredite."

    template = 'emails/estado_pedido_finalizado.html' if finalizado else 'emails/estado_pedido.html'

    estado = historial.estado
    estado = estado.capitalize()

    mail_data = {
        'url': f"{site_url}/usuario/ver_pedido/{token}",
        'img': f"{site_url}/static/img/mail.webp",
        'pedido_id': historial.merchant_order_id,
        'estado': estado,
        'mensaje': mensaje
    }
    enviar_mail_estado_pedido.delay(mail_data, user_email,template)

def mail_obs_comprobante_html(historial,observaciones):
    token = historial.token_consulta
    user_email = historial.facturacion.email
    pedido_id = historial.merchant_order_id
    site_url = f'{settings.SITE_URL}'
    mail_data = {
        'url': f"{site_url}/usuario/ver_pedido/{token}",
        'img' : f"{site_url}/static/img/mail.webp",
        'observaciones':observaciones,
        'pedido_id':pedido_id
    }
    enviar_mail_comprobante_obs.delay(mail_data,user_email)