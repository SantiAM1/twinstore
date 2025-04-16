from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import hashlib
import hmac
import urllib.parse
from django.contrib import messages
from django.contrib.auth import get_user_model

import requests

from django.urls import reverse

from core.decorators import bloquear_si_mantenimiento

from .models import HistorialCompras, PagoRecibidoMP
from cart.models import Carrito
from products.models import Producto
from users.forms import UsuarioForm
from users.models import PerfilUsuario,DatosFacturacion
from payment.forms import ComprobanteForm
from django.db import IntegrityError, transaction
from cart.decorators import requiere_carrito

import random
import string
from datetime import datetime

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

import logging
logger = logging.getLogger(__name__)

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

        secret = f"{settings.MP_WEBHOOK_KEY}"
        manifest = f"id:{dataID};request-id:{xRequestId};ts:{ts};"

        hmac_obj = hmac.new(secret.encode(), msg=manifest.encode(), digestmod=hashlib.sha256)
        sha = hmac_obj.hexdigest()

        if sha == hash_value:

            logger.info("HMAC verification passed")

            payment_id = request.GET.get("data.id") or request.GET.get("id")
            topic = request.GET.get("topic") or request.GET.get("type")
            if topic == "payment" and payment_id:

                url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
                headers = {
                    "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"
                }

                logger.info(f"🔎 Consultando pago con ID {payment_id}...")
                response = requests.get(url, headers=headers)
                
                pago_info = response.json()

                if response.status_code == 200:

                    logger.info(f"📥 Respuesta de Mercado Pago: {response.status_code}")

                    status = pago_info.get("status")
                    logger.info(f"!!! Estado del pago recibido: {status} !!!")

                    # * Metadata!!
                    metadata = pago_info.get('metadata', '')

                    logger.info(metadata)

                    if metadata:

                        logger.info('Metadata recibida correctamente!')
                        # * Lista de productos!
                        productos_metadata = metadata.get('productos','')
                        productos = []
                        for producto_id,cantidad in productos_metadata.items():
                            producto = get_object_or_404(Producto,id=int(producto_id))
                            productos.append({
                                'producto_id': producto.id,
                                'nombre':producto.nombre,
                                'precio_unitario':float(producto.precio),
                                'cantidad':cantidad,
                                'subtotal':float(producto.precio)*cantidad
                            })

                        # * Logica de usuarios, borrar el carrito si el pago no fue rechazado

                        if metadata['usuario'].get('user'):
                            User = get_user_model()
                            email = metadata['usuario'].get('user')
                            usuario = User.objects.get(email=email)
                            if status in ['approved', 'in_process', 'pending']:
                                carrito = Carrito.objects.filter(id=metadata['carrito_id']).first()
                                if carrito:
                                    carrito.pedidos.all().delete()
                                    carrito.delete()
                        else:
                            usuario = None
                            if not status == 'rejected':
                                session_key = metadata['usuario'].get('session')
                                store = SessionStore(session_key=session_key)
                                if 'carrito' in store:
                                    del store['carrito']
                                    store.save()

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
                                    'recibir_mail': metadata.get('recibir_mail', False),
                                }
                            )
                        except IntegrityError:
                            historial = HistorialCompras.objects.get(merchant_order_id=merchant_order_id)
                            creado = False

                        # * Creacion de los Datos de facturacion

                        if creado:
                            DatosFacturacion.objects.create(
                                historial=historial,
                                nombre=metadata['nombre'],
                                apellido=metadata['apellido'],
                                razon_social=metadata.get('razon_social', ''),
                                dni_cuit=metadata['dni_cuit'],
                                tipo_factura=metadata['tipo_factura'],
                                telefono=metadata.get('telefono', ''),
                                email=metadata['email'],
                                codigo_postal=metadata['codigo_postal'],
                                calle=metadata['calle'],
                            )
                    else:
                        logger.critical('Metadata no recibida!')

                    # * Almacenamos el pago recibido

                    PagoRecibidoMP.objects.update_or_create(
                    payment_id=payment_id,
                    defaults={
                        'merchant_order_id': pago_info.get("order", {}).get("id"),
                        'status': status,
                        'payer_email': pago_info.get("payer", {}).get("email"),
                        'transaction_amount': pago_info.get("transaction_amount"),
                        'payment_type': pago_info.get("payment_type_id"),
                        'external_reference':pago_info.get("external_reference"),
                        }
                    )
                else:
                    print(f"❌ Error al consultar pago {payment_id}")
        return HttpResponse(status=200)

def payment_success(request):
    merchant_order_id = request.GET.get('merchant_order_id','')
    historial = HistorialCompras.objects.filter(merchant_order_id=merchant_order_id).first()
    if not historial:
        return redirect('core:home')
    return render(request, 'payment/success.html',{'historial':historial})

@bloquear_si_mantenimiento
@requiere_carrito
def pedidos_efectivo_transferencia(request):
    if request.method == "POST":
        form = UsuarioForm(request.POST)
        if not form.is_valid():
            return redirect('core:home')
        
        data = form.cleaned_data
        forma_pago = request.POST.get('forma_pago')

        if forma_pago not in ['efectivo', 'transferencia']:
            return redirect("core:home")
        elif forma_pago == 'transferencia':
            merchant_order_id = generar_identificador_unico('T')
            status = 'pendiente'
        else:
            merchant_order_id = generar_identificador_unico('E')
            status = 'confirmado'

        if request.user.is_authenticated:
            carrito = Carrito.objects.filter(usuario=request.user).first()
            total_carrito = carrito.get_total()

            # * Armamos el detalle de productos
            productos = []
            for pedido in carrito.pedidos.all():
                productos.append({
                    'producto_id': pedido.producto.id,
                    'nombre': pedido.producto.nombre,
                    'precio_unitario': float(pedido.producto.precio),
                    'cantidad': pedido.cantidad,
                    'subtotal': float(pedido.get_total_precio()),
                })

            # * Borramos el carrito y pedidos
            carrito.pedidos.all().delete()
            carrito.delete()

            # * Guardamos los datos si el usuario lo desea
            if form.cleaned_data['guardar_datos']:
                perfil, create = PerfilUsuario.objects.get_or_create(user=request.user)
                perfil.tipo_factura = data['tipo_factura']
                perfil.dni_cuit = data['dni_cuit']
                perfil.razon_social = data['razon_social']
                perfil.nombre = data['nombre']
                perfil.apellido = data['apellido']
                perfil.calle = data['calle']
                perfil.calle_detail = data['calle_detail']
                perfil.cuidad = data['cuidad']
                perfil.provincia = data['provincia']
                perfil.codigo_postal = data['codigo_postal']
                perfil.telefono = data['telefono']
                perfil.guardar_datos = True
                perfil.save()
            else:
                perfil, create = PerfilUsuario.objects.get_or_create(user=request.user)
                perfil.guardar_datos = False
                perfil.save()

        else:
            carrito = request.session['carrito']
            if not carrito:
                return redirect('core:home')
            
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
            
            total_carrito = sum(producto['subtotal'] for producto in productos)

            # * Borrar el carrito
            del request.session['carrito']
            request.session.modified = True
            
        historial = HistorialCompras.objects.create(
        usuario=carrito.usuario if request.user.is_authenticated else None,
        productos=productos,
        total_compra=total_carrito,
        estado=status,
        forma_de_pago=forma_pago,
        merchant_order_id=merchant_order_id,
        recibir_mail=data['recibir_estado_pedido']
        )

        DatosFacturacion.objects.create(
            historial=historial,
            nombre=data['nombre'],
            apellido=data['apellido'],
            razon_social=data['razon_social'],
            dni_cuit=data['dni_cuit'],
            tipo_factura=data['tipo_factura'],
            telefono=data['telefono'],
            email=data['email'],
            codigo_postal=data['codigo_postal'],
            provincia=data['provincia'],
            calle=data['calle'],
            cuidad=data['cuidad'],
            calle_detail=data['calle_detail'],
        )

        return redirect(f"{reverse('payment:success')}?merchant_order_id={merchant_order_id}")

def subir_comprobante(request, token):
    historial = get_object_or_404(HistorialCompras, token_consulta=token)
    if request.method == 'POST':

        form = ComprobanteForm(request.POST, request.FILES)
        if form.is_valid():
            comprobante = form.save(commit=False)
            comprobante.historial = historial
            comprobante.save()
            messages.success(request, "✅ Comprobante subido correctamente. Lo revisaremos a la brevedad.")
            if request.user.is_authenticated:
                return redirect('users:mispedidos')
            return redirect('users:ver_pedidos',token=token)
        else:
            print(form.errors)
    else:
        form = ComprobanteForm()

    return render(request, 'payment/subir_comprobante.html', {'form': form, 'historial': historial})

def generar_identificador_pago(letra):
    fecha = datetime.now().strftime('%d%m%y')
    sufijo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{letra}-{fecha}-{sufijo}"

def generar_identificador_unico(letra):
    while True:
        nuevo_id = generar_identificador_pago(letra)
        if not HistorialCompras.objects.filter(merchant_order_id=nuevo_id).exists():
            return nuevo_id
        
def failure(request):
    return render(request,'payment/fail.html')

def pendings(request):
    return HttpResponse('Pendiente')