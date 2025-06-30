from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import hashlib
import hmac

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core import signing

import requests

from decimal import Decimal
from django.utils.timezone import now

from .models import HistorialCompras, PagoRecibidoMP,EstadoPedido,Cupon
from cart.models import Carrito
from products.models import Producto,ColorProducto
from users.models import DatosFacturacion
from payment.forms import ComprobanteForm
from django.db import IntegrityError, transaction
from cart.decorators import requiere_carrito

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

import logging
logger = logging.getLogger('mercadopago')

# -----WEBHOOK----- #
@csrf_exempt
def notification(request):
    if request.method == "POST":
        xSignature = request.headers.get("x-signature")
        xRequestId = request.headers.get("x-request-id")

        # ✅ Buscamos el ID dinámicamente según el tipo de notificación:
        dataID = request.GET.get("data.id") or request.GET.get("id")
        topic = request.GET.get("topic") or request.GET.get("type")

        logger.info(f"Webhook recibido - ID: {dataID}, Tipo: {topic}")

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
            logger.warning("Firma HMAC inválida")
            return HttpResponseBadRequest("Invalid signature format.")

        secret = f"{settings.MP_WEBHOOK_KEY}"
        manifest = f"id:{dataID};request-id:{xRequestId};ts:{ts};"

        hmac_obj = hmac.new(secret.encode(), msg=manifest.encode(), digestmod=hashlib.sha256)
        sha = hmac_obj.hexdigest()

        if sha == hash_value:

            logger.info("HMAC validado correctamente")

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

                if response.status_code == 200:

                    logger.info("Respuesta exitosa!")

                    status = pago_info.get("status")

                    logger.info(f"Estado de mercado pago {status}!")

                    _firma = pago_info.get("metadata", {})

                    if not _firma:
                        logger.warning("Metadata vacia")
                        return HttpResponse(status=400)
                    
                    firmado = _firma.get("firma")
                    try:
                        metadata = signing.loads(firmado)
                    except signing.BadSignature:
                        logger.warning("Firma inválida o manipulada")
                        return HttpResponseBadRequest("Firma inválida")

                    # * Lista de productos!
                    productos = generar_productos(metadata.get('productos'))

                    # * Obtener el usuario
                    user_data = metadata['usuario']
                    if user_data.get('id',''):
                        User = get_user_model()
                        id =  user_data.get('id')
                        usuario = User.objects.get(id=int(id))
                        key = None
                    else:
                        usuario = None
                        key = user_data.get('key')

                    # * Obtenemos el total de la compra
                    merchant_order_id = pago_info.get("order", {}).get("id")
                    order_url = f"https://api.mercadopago.com/merchant_orders/{merchant_order_id}"
                    order_response = requests.get(order_url, headers=headers)
                    order_info = order_response.json()

                    # Total de todos los pagos combinados:
                    total_real = order_info.get("total_amount")

                    # * Creacion de historial
                    try:
                        with transaction.atomic():
                            historial, creado = HistorialCompras.objects.get_or_create(
                            merchant_order_id=pago_info.get("order", {}).get("id"),
                            defaults={
                                'usuario': usuario,
                                'productos': productos,
                                'total_compra': total_real,
                                'estado': 'pendiente',
                                'forma_de_pago': 'mercado pago',
                                'recibir_mail': metadata.get('recibir_mail',False),
                            }
                        )
                    except IntegrityError:
                        historial = HistorialCompras.objects.get(merchant_order_id=merchant_order_id)
                        creado = False

                    logger.info(f"Historial {'creado' if creado else 'actualizado'} para orden: {merchant_order_id}")
                    # * Creacion de los Datos de facturacion
                    if creado:
                        try:
                            DatosFacturacion.objects.create(
                                historial=historial,
                                nombre=metadata['nombre'],
                                apellido=metadata['apellido'],
                                razon_social=metadata.get('razon_social', ''),
                                dni_cuit=metadata['dni_cuit'],
                                condicion_iva=metadata['condicion_iva'],
                                telefono=metadata.get('telefono', ''),
                                email=metadata['email'],
                                codigo_postal=metadata['codigo_postal'],
                                calle=metadata['calle'],
                            )
                        except Exception as e:
                            import traceback
                            logger.error(f"Error creando DatosFacturacion: {e}")
                            traceback.print_exc()

                    pago, creado = PagoRecibidoMP.objects.update_or_create(
                        payment_id=payment_id,
                        defaults={
                            'merchant_order_id': pago_info.get("order", {}).get("id"),
                            'status': status,
                            'payer_email': pago_info.get("payer", {}).get("email"),
                            'transaction_amount': pago_info.get("transaction_amount"),
                            'payment_type': pago_info.get("payment_type_id"),
                            'external_reference': pago_info.get("external_reference"),
                        }
                    )
                    cupon = metadata.get('cupon',None)
                    procesar_pago_y_estado(pago,usuario,cupon,key)
                else:
                    logger.error("Error al obtener datos de Mercado Pago")
        return HttpResponse(status=200)

def procesar_pago_y_estado(pago: PagoRecibidoMP,usuario,cupon=None,key=None):
    if not pago.merchant_order_id:
        return
    try:
        historial = HistorialCompras.objects.get(merchant_order_id=pago.merchant_order_id)
        if not historial.pagos.filter(pk=pago.pk).exists():
            historial.pagos.add(pago)
        pagos = historial.pagos.all()
        total_pagado = sum((p.transaction_amount or 0 for p in pagos if p.status == "approved"), Decimal('0.00'))

        estado_anterior = historial.estado

        comentario_extra = ""
        if all(p.status == "approved" for p in pagos):
            if total_pagado >= historial.total_compra:
                historial.estado = "confirmado"
                comentario_extra = " Comentario: ✔️ Pago completo."
            else:
                historial.estado = "pendiente"
                comentario_extra = " Comentario: ⚠️ Pago parcial."
        elif any(p.status == "rejected" for p in pagos):
            historial.estado = "rechazado"
        else:
            historial.estado = "pendiente"

        if estado_anterior != historial.estado:
            historial.requiere_revision = True
            historial.save(update_fields=["requiere_revision","estado"])

        EstadoPedido.objects.create(
            historial=historial,
            estado='Pago de mercado pago recibido (Servidor)',
            comentario=f'Total recibido: {pago.transaction_amount}.\nEstado del pago: {pago.status}.\nForma de pago: {pago.payment_type}.\n{comentario_extra}.\nEstado final del historial: {historial.estado}.'
        )
        
        logger.info(f"Forma de pago: {pago.payment_type}")
        logger.info(f"Total pagado: {total_pagado} / Total esperado: {historial.total_compra}")
        logger.info(f"Estado final del historial: {historial.estado}")

        if (pago.payment_type == 'ticket' and historial.estado == 'pendiente') or historial.estado == 'confirmado':
            if vaciar_carrito(usuario,key):
                logger.info(f"Carrito vaciado ({'usuario' if usuario else 'sesión'})")
            if cupon:
                try:
                    cupon = Cupon.objects.get(id=int(cupon))
                    EstadoPedido.objects.create(
                        historial=historial,
                        estado="Cupón Aplicado (Servidor)",
                        comentario=f"Cupón CÓDIGO #{cupon.codigo} del %{cupon.descuento} Aplicado en la compra"
                    )
                    cupon.delete()
                    logger.info(f"Cupon eliminado")
                except Cupon.DoesNotExist:
                    logger.error(f"El cupon enviado no existe")

    except HistorialCompras.DoesNotExist:
        return None

def vaciar_carrito(usuario,key=None):
    if key:
        store = SessionStore(session_key=key)
        if 'carrito' in store:
            del store['carrito']
            store.save()
            return True
    else:
        carrito = Carrito.objects.filter(usuario=usuario).first()
        if carrito:
            carrito.pedidos.all().delete()
            carrito.delete()
            return True
    return False

def generar_productos(data:dict) -> list:
    productos = []
    for producto_id,cantidad in data.items():
        producto_id_str, color_str = producto_id.split('-') 
        if color_str != 'null':
            try:
                color = get_object_or_404(ColorProducto, id=int(color_str))
            except ColorProducto.DoesNotExist:
                logger.error(f"Color no encontrado: {color_str}")
                color_str = 'null'
                color = None
        else:
            color = None
        producto = get_object_or_404(Producto,id=int(producto_id_str))
        nombre_producto = f"({color.nombre}) {producto.nombre}" if color_str != 'null' else producto.nombre
        productos.append({
            'sku': producto.sku,
            'nombre':nombre_producto,
            'precio_unitario':float(producto.precio),
            'cantidad':cantidad,
            'subtotal':float(producto.precio)*cantidad,
            'proveedor':producto.proveedor
        })
    return productos

def payment_success(request):
    merchant_order_id = request.GET.get('merchant_order_id','')
    historial = HistorialCompras.objects.filter(merchant_order_id=merchant_order_id).first()
    return render(request, 'payment/success.html',{'historial':historial})

def subir_comprobante(request, token):
    historial = get_object_or_404(HistorialCompras, token_consulta=token)
    if request.method == 'POST':

        form = ComprobanteForm(request.POST, request.FILES)
        if form.is_valid():
            comprobante = form.save(commit=False)
            comprobante.historial = historial
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