from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse,HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core import signing
from django.core.signing import BadSignature
from django.template.loader import render_to_string

from .models import HistorialCompras
from .forms import ComprobanteForm
from .webhook import (
    check_hmac_signature,
    requests_header,
    metadata_signed,
    crear_pago_mp,
    obtener_ticket,
    validar_ticket)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.throttling import SolicitarComprobante
from core.permissions import BloquearSiMantenimiento
from users.serializers import HistorialIdSerializer

import logging
logger = logging.getLogger('mercadopago')


class GenerarComprobante(APIView):
    permission_classes = [BloquearSiMantenimiento]
    throttle_classes = [SolicitarComprobante]

    def get(self, request: HttpRequest):
        serializer = HistorialIdSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            historial_id = signing.loads(data.get('id'))
        except BadSignature:
            return Response({'error': 'Firma inválida en el ID'}, status=status.HTTP_400_BAD_REQUEST)

        historial = HistorialCompras.objects.get(id=historial_id)

        if historial.forma_de_pago not in ['mixto','transferencia'] or historial.check_comprobante_subido():
            return Response({'error':'El comprobante ya fue subido'},status=status.HTTP_400_BAD_REQUEST)
        
        form = ComprobanteForm()
        modal_html = render_to_string("partials/comprobante-modal.html",{
            'historial': historial,
            'form': form
        },request=request)
        return Response({'modal': modal_html})

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

def payment_success(request):
    merchant_order_id = request.GET.get('merchant_order_id','')
    historial = HistorialCompras.objects.filter(merchant_order_id=merchant_order_id).first()
    return render(request, 'payment/success.html',{'historial':historial})

def subir_comprobante(request, id_signed):
    try:
        historial_id = signing.loads(id_signed)
    except BadSignature:
        return HttpResponse(status=404)
    
    historial = get_object_or_404(HistorialCompras, id=historial_id)
    if historial.forma_de_pago not in ['mixto','transferencia'] or historial.check_comprobante_subido():
        return HttpResponse(status=404)
    
    if request.method == 'POST':
        form = ComprobanteForm(request.POST, request.FILES)
        if form.is_valid():
            comprobante = form.save(commit=False)
            comprobante.historial = historial
            comprobante.save()
            messages.success(request, "Comprobante subido correctamente. Lo revisaremos a la brevedad.")
            return redirect('users:ver_pedidos',token=historial.token_consulta)
        else:
            messages.error(request,"Error al subir el comprobante.")
            return redirect('users:ver_pedidos',token=historial.token_consulta)
    
    return redirect("core:home")
        
def failure(request):
    return render(request,'payment/fail.html')

def pendings(request):
    return HttpResponse('Pendiente')