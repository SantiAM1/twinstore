from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import boto3
from botocore.exceptions import ClientError

def master_mail(user_email, subject, html_content):
    ses_client = boto3.client(
        'ses',
        aws_access_key_id=settings.AWS_SES_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SES_SECRET_ACCESS_KEY,
        region_name=settings.AWS_SES_REGION_NAME
    )

    try:
        response = ses_client.send_email(
            Source=settings.AWS_SES_SOURCE_EMAIL,
            Destination={'ToAddresses': [user_email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {'Data': html_content, 'Charset': 'UTF-8'}
                }
            }
        )
        return response['ResponseMetadata']['HTTPStatusCode']
    except ClientError as e:
        print(f"❌ Error al enviar mail: {e.response['Error']['Message']}")
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