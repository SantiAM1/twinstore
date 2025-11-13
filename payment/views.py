from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse,HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core import signing
from django.core.signing import BadSignature

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.permissions import BloquearSiMantenimiento
from core.throttling import ModalUsers
from cart.utils import preference_mp

from .templatetags.custom_filters import formato_pesos
from .serializers import ComprobanteSerializer,IntSigned
from .models import HistorialCompras,ComprobanteTransferencia,TicketDePago
from .webhook import (
    check_hmac_signature,
    requests_header,
    metadata_signed,
    crear_pago_mp,
    obtener_ticket,
    validar_ticket)

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

class DatosComprobante(APIView):
    permission_classes = [IsAuthenticated,BloquearSiMantenimiento]
    throttle_classes = [ModalUsers]
    def post(self, request: HttpRequest):
        serializer = IntSigned(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=400)
        id_signed = serializer.validated_data.get('numero_firmado')
        try:
            id_historial = signing.loads(id_signed)
        except BadSignature:
            return Response({"error": "ID de historial inválido."}, status=status.HTTP_400_BAD_REQUEST)
        
        historial = get_object_or_404(HistorialCompras, id=id_historial, usuario=request.user)
        monto = historial.monto_tranferir()

        return Response({'monto':formato_pesos(monto), 'id_firmado':id_signed}, status=status.HTTP_200_OK)

class SubirComprobante(APIView):
    permission_classes = [IsAuthenticated,BloquearSiMantenimiento]
    throttle_classes = [ModalUsers]
    def post(self, request: HttpRequest):
        serializer = ComprobanteSerializer(data=request.data)
        if not serializer.is_valid():
            messages.error(request, "Error al subir el comprobante.")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        comprobante_file = data.get('comprobante')
        id_signed = data.get('historial_id')

        try:
            id_historial = signing.loads(id_signed)
        except BadSignature:
            return Response({"error": "ID de historial inválido."}, status=status.HTTP_400_BAD_REQUEST)
        
        historial = get_object_or_404(HistorialCompras, id=id_historial, usuario=request.user)

        ComprobanteTransferencia.objects.create(
            historial=historial,
            file=comprobante_file
        )

        messages.success(request, "Comprobante subido exitosamente.")

        return Response({"reload":True},status=status.HTTP_200_OK)

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

class ArrepentimientoPostView(APIView):
    permission_classes = [IsAuthenticated,BloquearSiMantenimiento]
    throttle_classes = [ModalUsers]
    def post(self, request: HttpRequest):
        serializer = IntSigned(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=400)
        historial_signed = serializer.validated_data.get('numero_firmado')
        try:
            historial_id = signing.loads(historial_signed)
        except BadSignature:
            return Response({'error':'Firma inválida'},status=400)
        
        historial = get_object_or_404(HistorialCompras,id=historial_id,usuario=request.user)
        if not historial.verificar_arrepentimiento():
            return Response({'error':'No se puede solicitar el arrepentimiento'},status=400)
        
        historial.estado = 'arrepentido'
        historial.save()

        messages.success(request,'Arrepentimiento solicitado con éxito')

        return Response({'reload':True},status=200)

def payment_success(request):
    merchant_order_id = request.GET.get('merchant_order_id','')
    historial = HistorialCompras.objects.filter(merchant_order_id=merchant_order_id).first()
    return render(request, 'payment/success.html',{'historial':historial})

def failure(request):
    return render(request,'payment/fail.html')

def pendings(request):
    return HttpResponse('Pendiente')