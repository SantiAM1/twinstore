from django.conf import settings
from django.core import signing

from .models import PagoRecibidoMP,EstadoPedido,TicketDePago

from decimal import Decimal
import hmac
import hashlib
import requests

import logging
logger = logging.getLogger('mercadopago')

def check_hmac_signature(request) -> bool:
    """
    Verifica la firma HMAC enviada por mercado pago.
    Se utiliza en la validación del webhook
    """
    xSignature = request.headers.get("x-signature")
    xRequestId = request.headers.get("x-request-id")

    dataID = request.GET.get("data.id") or request.GET.get("id")
    topic = request.GET.get("topic") or request.GET.get("type")

    logger.info(f"Webhook recibido - ID: {dataID}, Tipo: {topic}")

    if not xSignature or not xRequestId or not dataID:
        return False

    parts = xSignature.split(",")
    ts = None
    hash_value = None

    for part in parts:
        keyValue = part.split("=", 1)
        if len(keyValue) == 2:
            key = keyValue[0].strip()
            value = keyValue[1].strip()
            if key == "ts":
                ts = value
            elif key == "v1":
                hash_value = value

    if not ts or not hash_value:
        logger.warning("Firma HMAC inválida")
        return False

    secret = f"{settings.MP_WEBHOOK_KEY}"
    manifest = f"id:{dataID};request-id:{xRequestId};ts:{ts};"

    hmac_obj = hmac.new(secret.encode(), msg=manifest.encode(), digestmod=hashlib.sha256)
    sha = hmac_obj.hexdigest()

    if sha != hash_value:
        return False
        
    return True

def requests_header(request):
    payment_id = request.GET.get("data.id") or request.GET.get("id")
    topic = request.GET.get("topic") or request.GET.get("type")
    if topic == "payment" and payment_id:

        url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
        headers = {
            "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"
        }
        response = requests.get(url, headers=headers)
        pago_info = response.json()

        logger.info(f"Procesando pago ID: {payment_id}, estado: {response.status_code}")

        return pago_info,response.status_code,headers,payment_id
    
    return None,None

def metadata_signed(pago_info):
    _firma = pago_info.get("metadata", {})
    if not _firma:
        logger.warning("Metadata vacia")
        return
    
    firmado = _firma.get("firma")
    try:
        metadata = signing.loads(firmado)
        return metadata
    except signing.BadSignature:
        logger.warning("Firma inválida o manipulada")
        return

def crear_pago_mp(payment_id,pago_info,status,merchant_order_id):
    pago, _ = PagoRecibidoMP.objects.update_or_create(
        payment_id=payment_id,
        defaults={
            'merchant_order_id': merchant_order_id,
            'status': status,
            'payer_email': pago_info.get("payer", {}).get("email"),
            'transaction_amount': pago_info.get("transaction_amount"),
            'payment_type': pago_info.get("payment_type_id"),
            'external_reference': pago_info.get("external_reference"),
        }
    )
    return pago

def obtener_ticket(id,merchant_order_id):
    try:
        ticket = TicketDePago.objects.get(id=int(id))
        if not ticket.merchant_order_id:
            ticket.merchant_order_id = merchant_order_id
            ticket.save()
            logger.info(f"Ticket obtenido con exito")
        return ticket
    except TicketDePago.DoesNotExist:
        logger.error(f"El ticket con id:{id} no fue encontrado")
        return

def validar_ticket(ticket:TicketDePago,merchant_order_id):
    monto_a_validar = ticket.monto
    historial = ticket.historial

    pagos = PagoRecibidoMP.objects.filter(merchant_order_id=merchant_order_id)
    total_pagado = sum((p.transaction_amount or 0 for p in pagos if p.status == "approved"), Decimal('0.00'))

    estado_anterior = ticket.estado
    comentario_extra = ""
    if all(p.status == "approved" for p in pagos):
        if total_pagado >= monto_a_validar:
            ticket.estado = "aprobado"
            comentario_extra = " Ticket: ✔️ Pago completo."
        else:
            ticket.estado = "pendiente"
            comentario_extra = " Ticket: ⚠️ Pago parcial."
    elif any(p.status == "rejected" for p in pagos):
        ticket.estado = "rechazado"
    else:
        ticket.estado = "pendiente"

    if estado_anterior != ticket.estado:
        ticket.save()

    logger.info(f"Total pagado: {total_pagado} / Total esperado: {ticket.monto}")
    logger.info(f"Estado final del Ticket: {ticket.estado}")

    EstadoPedido.objects.create(
        historial=historial,
        estado='Pago de mercado pago recibido (Servidor)',
        comentario=f'Ticket pagado: ID:#{ticket.merchant_order_id}.\nEstado del ticket: {ticket.estado}.\n{comentario_extra}.'
    )
