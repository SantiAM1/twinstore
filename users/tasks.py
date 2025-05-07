from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient

def master_mail(user_email,subject,html_content):
    message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=user_email,
        subject=subject,
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        print("❌ Error al enviar mail de confirmación:", e)
        return None

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

    html_content = render_to_string('emails/compra_exitosa.html', context)
    subject = 'Compra recibida - Twinstore'

    return master_mail(user_email,subject,html_content)

@shared_task
def enviar_mail_confirm_user(mail_data,user_email):
    context = {
        'url' : mail_data['url'],
        'img' : mail_data['img']
    }

    html_content = render_to_string('emails/bienvenida_usuario.html', context)
    subject="Confirmá tu cuenta en Twinstore"

    return master_mail(user_email,subject,html_content)

@shared_task
def enviar_mail_estado_pedido(mail_data,user_email,template):
    context = {
        'url' : mail_data['url'],
        'img' : mail_data['img'],
        'pedido_id': mail_data['pedido_id'],
        'estado': mail_data['estado'],
        'mensaje': mail_data['mensaje'],
    }

    html_content = render_to_string(template, context)
    subject='Estado de tu pedido - Twinstore'

    return master_mail(user_email,subject,html_content)

@shared_task
def enviar_mail_comprobante_obs(mail_data,user_email):
    context = {
        'url' : mail_data['url'],
        'img' : mail_data['img'],
        'pedido_id': mail_data['pedido_id'],
        'observaciones': mail_data['observaciones'],
    }

    html_content = render_to_string('emails/comprobantes_obs.html', context)
    subject='Observaciones Comprobante - Twinstore'

    return master_mail(user_email,subject,html_content)

@shared_task
def enviar_mail_reset_password(context):
    url = context['url']
    user_email = context['email']
    text_message = f"Hola, para recuperar tu contraseña hacé clic en el siguiente enlace:\n{url}"

    return master_mail(
        user_email=user_email,
        subject='Recuperar tu contraseña - Twinstore',
        html_content=f"<p>{text_message}</p>"
    )