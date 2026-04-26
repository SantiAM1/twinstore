from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse,HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.core import signing
from django.core.signing import BadSignature

from rest_framework.views import APIView
from rest_framework.response import Response

from core.permissions import BloquearSiMantenimiento
from core.throttling import ModalUsers
from payment.utils import preference_mp
from orders.models import Venta

from .models import TicketDePago
from .webhook import (
    check_hmac_signature,
    requests_header,
    metadata_signed,
    crear_pago_mp,
    obtener_ticket,
    validar_ticket)
from .serializers import IntSigned

import logging
logger = logging.getLogger('mercadopago')

# -----WEBHOOK----- #
@csrf_exempt
def webhook_mercadopago(request):
    if request.method == "POST":
        if not check_hmac_signature(request):
            return HttpResponse(status=200)
        
        logger.info("HMAC validado correctamente")
        pago_info,status_code,headers,payment_id = requests_header(request)
        
        if pago_info == None and status_code == None:
            return HttpResponse(status=200)

        if status_code != 200:
            logger.error("Error al obtener datos de Mercado Pago")
            return HttpResponse(status=200)
        
        logger.info("Respuesta exitosa!")
        status = pago_info.get("status")
        logger.info(f"Estado de mercado pago '{status}'!")

        metadata = metadata_signed(pago_info)
        if not metadata:
            return HttpResponse(status=400)
        
        # * Obtenemos el id
        merchant_order_id = pago_info.get("order", {}).get("id")

        # * Creamos el pago de mercado pago
        crear_pago_mp(payment_id,pago_info,status,merchant_order_id)

        # * Obtenemos el ticket
        ticket = obtener_ticket(metadata.get('ticket'), merchant_order_id)
        if ticket:
            # * Validamos el ticket
            validar_ticket(ticket, merchant_order_id)
        else:
            logger.warning(f"Intento de validar ticket inválido: {metadata.get('ticket')}")

        return HttpResponse(status=200)

class InitPointMPView(APIView):
    permission_classes = [BloquearSiMantenimiento]
    throttle_classes = [ModalUsers]
    def post(self,request):
        serializer = IntSigned(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=400)
        
        numero_firmado = serializer.validated_data.get('numero_firmado')

        try:
            ticket_id = signing.loads(numero_firmado)
        except BadSignature:
            return Response({'error': 'Firma inválida'}, status=400)

        try:
            ticket = TicketDePago.objects.get(id=ticket_id)
            if ticket.estado == 'aprobado':
                return Response(status=400)
            data = ticket.get_preference_data()
            metadata = data.get('metadata')
            firma = {"firma":signing.dumps(metadata)}

            try:
                preference = preference_mp(data['numero'],data['ticket_id'],data['dni_cuit'],data['ident_type'],data['email'],data['nombre'],data['apellido'],data['codigo_postal'],data['calle_nombre'],data['calle_altura'],firma,backurl_success=data['backurl_success'],backurl_fail=data['backurl_fail'])
                init_point = preference.get("init_point", "")
                return Response({'init_point':init_point},status=200)
            except ValueError as e:
                return Response({'error': str(e)}, status=500)
            
        except TicketDePago.DoesNotExist:
            return Response(status=404)

def payment_success(request):
    merchant_order_id = request.GET.get('merchant_order_id','')
    venta = Venta.objects.filter(merchant_order_id=merchant_order_id).first()
    return render(request, 'payment/success.html',{'venta':venta})

def failure(request):
    return render(request,'payment/fail.html')

def pendings(request):
    return HttpResponse('Pendiente')