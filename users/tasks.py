from celery import shared_task
from django.template.loader import render_to_string
from django.conf import settings
import boto3
from botocore.exceptions import ClientError
from core.utils import build_absolute_uri
from django_tenants.utils import schema_context

def get_mail_imgs() -> dict:
    """
    Construye un diccionario con las URLs de las imágenes utilizadas en los correos electrónicos.

    ```json 
    {
        'insta': 'URL de la imagen de Instagram',
        'tiktok': 'URL de la imagen de TikTok',
        'link': 'URL de la imagen de LinkedIn',
        'success': 'URL de la imagen de éxito',
        'star': 'URL de la imagen de estrella',
    }
    """
    images = {
        'insta': f"{build_absolute_uri()}/static/img/mails/insta-64.png",
        'tiktok': f"{build_absolute_uri()}/static/img/mails/tiktok-64.png",
        'link': f"{build_absolute_uri()}/static/img/mails/link-64.png",
        'success': f"{build_absolute_uri()}/static/img/mails/check-64.png",
        'star': f"{build_absolute_uri()}/static/img/mails/star.png",
    }
    return images

def master_mail(user_email, subject, html_content):
    """
    Función maestra para enviar correos electrónicos utilizando AWS SES
    """
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
def enviar_mail_compra(venta_data, user_email,schema_name):
    with schema_context(schema_name):
        context = {
            'url': venta_data['url'],
            'codigo': venta_data['codigo'],
            'compra':venta_data['compra'],
            'adicional':venta_data['adicional'],
            'total':venta_data['total']
        }

        images = get_mail_imgs()
        context.update(images)

        html_content = render_to_string('emails/compra.html', context)
        subject = 'Compra recibida - Twinstore'

        return master_mail(user_email,subject,html_content)

@shared_task
def enviar_mail_confirm_user(mail_data,user_email,schema_name):
    with schema_context(schema_name):
        context = {
            'codigo' : mail_data['codigo'],
            'username': mail_data['username']
        }

        images = get_mail_imgs()
        context.update(images)

        html_content = render_to_string('emails/welcome.html', context)
        subject="Confirmá tu cuenta en Twinstore"

        return master_mail(user_email,subject,html_content)

@shared_task
def enviar_mail_recuperar_cuenta(mail_data,user_email,schema_name):
    with schema_context(schema_name):
        context = {
            'codigo' : mail_data['codigo'],
            'username': mail_data['username']
        }

        images = get_mail_imgs()
        context.update(images)

        html_content = render_to_string('emails/recuperar.html', context)
        subject="Recuperá tu cuenta en Twinstore"

        return master_mail(user_email,subject,html_content)

@shared_task
def enviar_mail_estado_pedido(mail_data,user_email,template,schema_name):
    with schema_context(schema_name):
        context = {
            'url' : mail_data['url'],
            'codigo': mail_data['codigo'],
            'estado': mail_data['estado'],
        }

        images = get_mail_imgs()
        context.update(images)

        html_content = render_to_string(template, context)
        subject=f'#{context["codigo"]} - Twinstore'

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
def enviar_reseña_token_html(mail_data,user_email,template, schema_name):
    with schema_context(schema_name):
        context = {
            'url' : mail_data['url'],
            'producto': mail_data['producto'],
            'username': mail_data['username'],
            'img_prod': mail_data['img_prod'],
        }

        images = get_mail_imgs()
        context.update(images)

        html_content = render_to_string(template, context)
        subject='Dejanos tu reseña - Twinstore'

        return master_mail(user_email,subject,html_content)