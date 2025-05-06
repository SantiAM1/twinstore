from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

@shared_task
def enviar_mail_compra(historial_data, user_email):
    context = {
        'url': historial_data['url'],
        'img': historial_data['img'],
        'token': historial_data['token'],
        'productos':historial_data['productos'],
        'adicional':historial_data['adicional'],
        'total':historial_data['total']
    }

    html = render_to_string('emails/compra_exitosa.html', context)
    text = f"Gracias por tu compra! Este es tu código de seguimiento: {historial_data['token']}"

    msg = EmailMultiAlternatives(
        subject='Compra recibida - Twinstore',
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()

@shared_task
def enviar_mail_confirm_user(mail_data,user_email):
    context = {
        'url' : mail_data['url'],
        'img' : mail_data['img']
    }

    html = render_to_string('emails/bienvenida_usuario.html', context)
    text = f'Hola {user_email}, para verificar tu cuenta hacé clic en: {mail_data["url"]}'

    msg = EmailMultiAlternatives(
        subject='Confirmá tu cuenta en Twinstore',
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()

@shared_task
def enviar_mail_estado_pedido(mail_data,user_email,template):
    context = {
        'url' : mail_data['url'],
        'img' : mail_data['img'],
        'pedido_id': mail_data['pedido_id'],
        'estado': mail_data['estado'],
        'mensaje': mail_data['mensaje'],
    }

    html = render_to_string(template, context)
    text = f"Hola {user_email}, esto es el estado de tu pedido ID:#{mail_data['pedido_id']}: {mail_data['estado']}"

    msg = EmailMultiAlternatives(
        subject='Estado de tu pedido - Twinstore',
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()

@shared_task
def enviar_mail_comprobante_obs(mail_data,user_email):
    context = {
        'url' : mail_data['url'],
        'img' : mail_data['img'],
        'pedido_id': mail_data['pedido_id'],
        'observaciones': mail_data['observaciones'],
    }

    html = render_to_string('emails/comprobantes_obs.html', context)
    text = f"Hola {user_email}, queremos contarte que el pedido con ID:#{mail_data['pedido_id']} ha sido rechazado. Observaciones: {mail_data['observaciones']}"

    msg = EmailMultiAlternatives(
        subject='Observaciones Comprobante - Twinstore',
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()

@shared_task
def enviar_mail_reset_password(context):
    url = context['url']
    user_email = context['email']
    text_message = f"Link de recuperación: {url}"
    
    msg = EmailMultiAlternatives(
        subject='Recuperar tu contraseña - Twinstore',
        body=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email]
    )
    msg.send()