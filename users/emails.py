from django.conf import settings
from django.contrib.auth.models import User
from .tasks import enviar_mail_compra,enviar_mail_confirm_user,enviar_mail_estado_pedido,enviar_mail_comprobante_obs,enviar_mail_recuperar_cuenta,enviar_reseña_token_html
from .decorators import debug_pass

@debug_pass
def mail_confirm_user_html(usuario:User) -> None:
    """
    Envía el mail de confirmación de cuenta
    """
    token = usuario.token_usuario.latest('creado')
    mail_data = {
        'codigo' : token.codigo,
        'username': usuario.perfil.nombre
    }
    enviar_mail_confirm_user.delay(mail_data,user_email=usuario.email)

@debug_pass
def mail_recuperar_cuenta_html(usuario:User) -> None:
    """
    Envía el mail de recuperación de cuenta
    """
    token = usuario.token_usuario.latest('creado')
    mail_data = {
        'codigo' : token.codigo,
        'username': usuario.perfil.nombre
    }
    enviar_mail_recuperar_cuenta.delay(mail_data,user_email=usuario.email)

@debug_pass
def mail_buy_send_html(historial,user_email):
    """
    Envía el mail de compra exitosa
    """
    codigo = historial.merchant_order_id
    site_url = f'{settings.SITE_URL}'
    compra = historial.productos
    adicional = historial.get_adicional()
    total = historial.total_compra
    historial_data = {
    'url': f"{site_url}/usuario/pedido/{codigo}",
    'codigo': codigo,
    'compra':compra,
    'adicional':adicional,
    'total':total
    }
    enviar_mail_compra.delay(historial_data, user_email)

@debug_pass
def mail_estado_pedido_html(historial,user_email):
    """Envía el mail cuando hay un cambio en el estado del pedido"""
    codigo = historial.merchant_order_id
    site_url = f'{settings.SITE_URL}'

    estado = historial.estado
    estado = estado.capitalize()

    mail_data = {
        'url': f"{site_url}/usuario/pedido/{codigo}",
        'codigo': codigo,
        'estado': estado,
    }
    enviar_mail_estado_pedido.delay(mail_data, user_email,'emails/estado_pedido.html')

@debug_pass
def reseña_token_html(token_usuario,user_email):
    """Envía el mail con el token para dejar una reseña"""
    site_url = f'{settings.SITE_URL}'

    mail_data = {
        'url': f"{site_url}/usuario/reviews/{token_usuario.token}",
        'producto': token_usuario.producto.nombre,
        'username': token_usuario.usuario.nombre,
        'img_prod': f"{settings.SITE_URL}{token_usuario.producto.get_portada_600()}",
    }
    enviar_reseña_token_html.delay(mail_data, user_email,'emails/review.html')

@debug_pass
def mail_obs_comprobante_html(historial,observaciones):
    token = historial.merchant_order_id
    user_email = historial.facturacion.email
    pedido_id = historial.merchant_order_id
    site_url = f'{settings.SITE_URL}'
    mail_data = {
        'url': f"{site_url}/usuario/ver_pedido/{token}",
        'observaciones':observaciones,
        'pedido_id':pedido_id
    }
    enviar_mail_comprobante_obs.delay(mail_data,user_email)
