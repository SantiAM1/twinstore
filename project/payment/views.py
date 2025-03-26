from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.views.decorators.csrf import csrf_exempt

import hashlib
import hmac
import urllib.parse

import requests

from .models import HistorialCompras, PagoRecibido
from cart.models import Carrito
from products.models import Producto

# -----WEBHOOK----- #
@csrf_exempt
def notification(request):
    if request.method == "POST":
        xSignature = request.headers.get("x-signature")
        xRequestId = request.headers.get("x-request-id")

        # ✅ Buscamos el ID dinámicamente según el tipo de notificación:
        dataID = request.GET.get("data.id") or request.GET.get("id")
        topic = request.GET.get("topic") or request.GET.get("type")

        if not xSignature or not xRequestId or not dataID:
            return HttpResponseBadRequest("Missing required headers or parameters.")

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
            return HttpResponseBadRequest("Invalid signature format.")

        # Armamos el manifest usando dataID, sea payment o merchant_order
        secret = f"{settings.MP_WEBHOOK_KEY}"
        manifest = f"id:{dataID};request-id:{xRequestId};ts:{ts};"

        hmac_obj = hmac.new(secret.encode(), msg=manifest.encode(), digestmod=hashlib.sha256)
        sha = hmac_obj.hexdigest()

        if sha == hash_value:
            print(f"✅ HMAC verification passed (topic: {topic})")
            print("Webhook recibido:", request.GET.dict())
            payment_id = request.GET.get("data.id") or request.GET.get("id")
            topic = request.GET.get("topic") or request.GET.get("type")
            if topic == "payment" and payment_id:
                # Consultamos el pago en Mercado Pago
                url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
                headers = {
                    "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"
                }

                print(f"🔎 Consultando pago con ID {payment_id}...")
                response = requests.get(url, headers=headers)
                print(f"📥 Respuesta de Mercado Pago: {response.status_code}")
                pago_info = response.json()

                if response.status_code == 200:
                    status = pago_info.get("status")
                    print(f"✅ Estado del pago recibido: {status}")

                    if status == "approved":
                        PagoRecibido.objects.update_or_create(
                        payment_id=payment_id,
                        defaults={
                            'merchant_order_id': pago_info.get("order", {}).get("id"),
                            'status': status,
                            'payer_email': pago_info.get("payer", {}).get("email"),
                            'transaction_amount': pago_info.get("transaction_amount"),
                            'payment_type': pago_info.get("payment_type_id"),
                            }
                        )
                    else:
                        print(f"⚠️ El pago {payment_id} no está aprobado (estado: {status}).")
                else:
                    print(f"❌ Error al consultar pago {payment_id}")
        return HttpResponse(status=200)

def pendings(request):
    return HttpResponse('Pendiente')

def payment_success(request):
    payment_id = request.GET.get('payment_id')
    merchant_order_id = request.GET.get('merchant_order_id')
    historial_existente = HistorialCompras.objects.filter(payment_id=payment_id).first()
    if historial_existente:
        return redirect('core:home')
    pago_recibido = PagoRecibido.objects.filter(payment_id=payment_id, status="approved").first()
    status = 'confirmado' if pago_recibido else 'pendiente'
    if request.user.is_authenticated:
        #step Si esta autenticado
        carrito = Carrito.objects.filter(usuario=request.user).first()
        historial = crear_historial(carrito,payment_id,merchant_order_id,status)
        # * Borramos el carrito
        carrito.pedidos.all().delete()
        carrito.delete()
    else:
        #step No esta autenticado
        carrito = request.session['carrito']
        historial = crear_historial_session(carrito,payment_id,merchant_order_id,status)
        # * Borrar el carrito
        del request.session['carrito']
        request.session.modified = True
    token = historial.token_consulta
    return render(request,'payment/success.html',{'token':token})

def failure(request):
    return render(request,'payment/fail.html')

def crear_historial_session(carrito, payment_id, merchant_order_id,status):
    productos = []
    for producto_id,cantidad in carrito.items():
        producto = get_object_or_404(Producto,id=int(producto_id))
        productos.append({
            'producto_id': producto.id,
            'nombre':producto.nombre,
            'precio_unitario':float(producto.precio),
            'cantidad':cantidad,
            'subtotal':float(producto.precio)*cantidad
        })
    total_pagado = sum(producto['subtotal'] for producto in productos)
    historial = HistorialCompras.objects.create(
        productos=productos,
        total_pagado=total_pagado,
        estado=status,
        payment_id=payment_id,
        merchant_order_id=merchant_order_id,
        fecha_compra=timezone.now()
    )
    print(f"✅ Historial pendiente creado para usuario anonimo")
    return historial

def crear_historial(carrito, payment_id, merchant_order_id,status):
    # Armamos la estructura con los productos del carrito
    productos = []
    for pedido in carrito.pedidos.all():
        productos.append({
            'producto_id': pedido.producto.id,
            'nombre': pedido.producto.nombre,
            'precio_unitario': float(pedido.producto.precio),
            'cantidad': pedido.cantidad,
            'subtotal': float(pedido.get_total_precio()),
        })

    total_pagado = carrito.get_total()

    # Creamos el historial en estado pendiente
    historial = HistorialCompras.objects.create(
        usuario=carrito.usuario,  # Puede ser None si es carrito anónimo
        productos=productos,
        total_pagado=total_pagado,
        estado=status,
        payment_id=payment_id,
        merchant_order_id=merchant_order_id,
        fecha_compra=timezone.now()
    )
    print(f"✅ Historial pendiente creado para usuario {carrito.usuario if carrito.usuario else 'Anónimo'}")
    return historial
