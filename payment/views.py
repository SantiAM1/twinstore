from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core import signing

from .models import HistorialCompras
from .forms import ComprobanteForm
from .webhook import (
    check_hmac_signature,
    requests_header,
    metadata_signed,
    generar_productos,
    user_key,
    total_merchant,
    crear_historial,
    procesar_pago_y_estado,
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

        if status_code == 200:
            logger.info("Respuesta exitosa!")
            status = pago_info.get("status")
            logger.info(f"Estado de mercado pago '{status}'!")

            metadata = metadata_signed(pago_info)
            if not metadata:
                return HttpResponse(status=400)
            
            # * Obtenemos el total de la compra y el id
            total_real,merchant_order_id = total_merchant(pago_info,headers)

            # * Creamos el pago de mercado pago
            pago = crear_pago_mp(payment_id,pago_info,status,merchant_order_id)

            if metadata.get('productos'):
                # * Lista de productos
                productos = generar_productos(metadata.get('productos'))

                # * Usuario | Session key
                usuario,key = user_key(metadata)

                # * Creacion de historial y datos de facturacion
                crear_historial(merchant_order_id,usuario,productos,total_real,metadata)

                # * Obtenemos el cupon (Si fue utilizado)
                cupon = metadata.get('cupon',None)

                # * Analisis final del la compra
                procesar_pago_y_estado(pago,usuario,cupon,key)

            elif metadata.get('ticket'):
                # * Obtenemos el ticket
                ticket = obtener_ticket(metadata.get('ticket'), merchant_order_id)
                if ticket:
                    # * Validamos el ticket!
                    validar_ticket(ticket, merchant_order_id)
                else:
                    logger.warning(f"Intento de validar ticket inválido: {metadata.get('ticket')}")
        else:
            logger.error("Error al obtener datos de Mercado Pago")

        return HttpResponse(status=200)

def payment_success(request):
    merchant_order_id = request.GET.get('merchant_order_id','')
    historial = HistorialCompras.objects.filter(merchant_order_id=merchant_order_id).first()
    return render(request, 'payment/success.html',{'historial':historial})

def subir_comprobante(request, token):
    historial = get_object_or_404(HistorialCompras, token_consulta=token)
    if historial.forma_de_pago not in ['mixto','transferencia'] or historial.comprobante:
        return HttpResponse(status=404)
    if request.method == 'POST':
        form = ComprobanteForm(request.POST, request.FILES)
        if form.is_valid():
            comprobante = form.save(commit=False)
            comprobante.historial = historial
            if historial.forma_de_pago == 'mixto':
                ticket = historial.tickets.filter(tipo='transferencia').first()
                comprobante.ticket = ticket
            comprobante.save()
            messages.success(request, "Comprobante subido correctamente. Lo revisaremos a la brevedad.")
            if request.user.is_authenticated:
                return redirect('users:mispedidos')
            return redirect('users:ver_pedidos',token=token)
        else:
            messages.error(request,"Error al subir el comprobante.")
            return redirect('users:ver_pedidos',token=token)
    else:
        form = ComprobanteForm()

    return render(request, 'payment/subir_comprobante.html', {'form': form, 'historial': historial})
        
def failure(request):
    return render(request,'payment/fail.html')

def pendings(request):
    return HttpResponse('Pendiente')