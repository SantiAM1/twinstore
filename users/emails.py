from django.conf import settings
from .tasks import enviar_mail_compra,enviar_mail_confirm_user,enviar_mail_estado_pedido,enviar_mail_comprobante_obs,enviar_mail_recuperar_cuenta,enviar_reseña_token_html
from .decorators import debug_pass
from core.utils import build_absolute_uri
from django.db import connection

@debug_pass
def mail_confirm_user_html(usuario) -> None:
    """
    Envía el mail de confirmación de cuenta
    """
    token = usuario.token_usuario.latest('creado')
    mail_data = {
        'codigo' : token.codigo,
        'username': usuario.first_name
    }

    schema_name = getattr(connection, 'schema_name', 'public')

    enviar_mail_confirm_user.delay(mail_data,usuario.email,schema_name)

@debug_pass
def mail_recuperar_cuenta_html(usuario) -> None:
    """
    Envía el mail de recuperación de cuenta
    """
    token = usuario.token_usuario.latest('creado')
    mail_data = {
        'codigo' : token.codigo,
        'username': usuario.first_name
    }

    schema_name = getattr(connection, 'schema_name', 'public')

    enviar_mail_recuperar_cuenta.delay(mail_data,usuario.email,schema_name)

@debug_pass
def mail_buy_send_html(venta,user_email):
    """
    Envía el mail de compra exitosa
    """
    codigo = venta.merchant_order_id
    site_url = f'{build_absolute_uri()}'
    compra = venta.productos
    adicional = venta.get_adicional()
    total = venta.total_compra
    venta_data = {
    'url': f"{site_url}/usuario/pedido/{codigo}",
    'codigo': codigo,
    'compra':compra,
    'adicional':adicional,
    'total':total
    }

    schema_name = getattr(connection, 'schema_name', 'public')

    enviar_mail_compra.delay(venta_data, user_email,schema_name)

@debug_pass
def mail_estado_pedido_html(venta,user_email):
    """Envía el mail cuando hay un cambio en el estado del pedido"""
    codigo = venta.merchant_order_id
    url_pedido = build_absolute_uri(path=f"/usuario/pedido/{codigo}")

    estado = venta.estado.capitalize()

    mail_data = {
        'url': url_pedido,
        'codigo': codigo,
        'estado': estado,
    }

    schema_name = getattr(connection, 'schema_name', 'public')

    enviar_mail_estado_pedido.delay(mail_data, user_email,'emails/estado_pedido.html',schema_name)

@debug_pass
def reseña_token_html(token_usuario,user_email):
    """Envía el mail con el token para dejar una reseña"""
    site_url = f'{build_absolute_uri()}'

    mail_data = {
        'url': f"{site_url}/usuario/reviews/{token_usuario.token}",
        'producto': token_usuario.producto.nombre,
        'username': token_usuario.usuario.first_name,
        'img_prod': f"{build_absolute_uri()}{token_usuario.producto.get_portada_600()}",
    }

    schema_name = getattr(connection, 'schema_name', 'public')

    enviar_reseña_token_html.delay(mail_data, user_email,'emails/review.html',schema_name)

@debug_pass
def mail_obs_comprobante_html(venta,observaciones):
    token = venta.merchant_order_id
    user_email = venta.facturacion.email
    pedido_id = venta.merchant_order_id
    site_url = f'{build_absolute_uri()}'
    mail_data = {
        'url': f"{site_url}/usuario/ver_pedido/{token}",
        'observaciones':observaciones,
        'pedido_id':pedido_id
    }
    enviar_mail_comprobante_obs.delay(mail_data,user_email)
