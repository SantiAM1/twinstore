from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404,render
from django.conf import settings
from django.utils import timezone
from django.templatetags.static import static
from django.template.loader import render_to_string
from django.urls import reverse

from users.forms import UsuarioForm
from users.models import PerfilUsuario,DatosFacturacion

from core.permissions import BloquearSiMantenimiento
from core.decorators import bloquear_si_mantenimiento
from core.throttling import EnviarWtapThrottle,CarritoThrottle,CalcularPedidoThrottle

from payment.models import HistorialCompras

from .models import Producto, Carrito, Pedido
import mercadopago

from .serializers import CalcularPedidoSerializer,AgregarAlCarritoSerializer,EliminarPedidoSerializer,ActualizarPedidoSerializer
from .context_processors import carrito_total
from .permissions import TieneCarrito
from .decorators import requiere_carrito


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import re
from weasyprint import HTML
import datetime
import os
import base64
import pytz
import uuid
from datetime import timedelta
import random
import string
from datetime import datetime

# ----- APIS ----- #
class EnviarWtapView(APIView):
    permission_classes = [BloquearSiMantenimiento]
    throttle_classes = [EnviarWtapThrottle]
    def get(self,request):
        productos = []

        if request.user.is_authenticated:
            carrito = get_object_or_404(Carrito, usuario=request.user)
            pedidos = carrito.pedidos.select_related('producto')
            direccion = request.user.perfil.calle
            codigo_postal = request.user.perfil.codigo_postal
            for pedido in pedidos:
                productos.append({
                    "nombre": pedido.producto.nombre,
                    "cantidad": pedido.cantidad
                })
        else:
            direccion = ""
            codigo_postal = ""
            carrito_sesion = request.session.get('carrito', {})
            for pedido_id, cantidad in carrito_sesion.items():
                try:
                    producto = Producto.objects.get(id=pedido_id)
                    productos.append({
                        "nombre": producto.nombre,
                        "cantidad": cantidad
                    })
                except Producto.DoesNotExist:
                    continue

        return Response({"productos": productos,'direccion':direccion,'codigo_postal':codigo_postal})
class ActualizarPedidoView(APIView):
    permission_classes = [TieneCarrito,BloquearSiMantenimiento]
    throttle_classes = [CarritoThrottle]
    def post(self,request):
        serializer = ActualizarPedidoSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            action = data['action']
            pedido_id = data['pedido_id']

            if request.user.is_authenticated:
                carrito = get_object_or_404(Carrito, usuario=request.user)
                pedido = get_object_or_404(Pedido, id=pedido_id, carrito=carrito)
                #* Si se cambian las cantidad se actualiza
                if action == "increment":
                    if pedido.cantidad < 5:
                        pedido.cantidad += 1
                        pedido.save()
                elif action == "decrement":
                    if pedido.cantidad > 1:
                        pedido.cantidad -= 1
                        pedido.save()
                    else:
                        pedido.delete()
                        pedido = None
                cantidad = pedido.cantidad if pedido else 0
            else:
                carrito = request.session.get('carrito',{})
                pedido_key = str(pedido_id)
                if pedido_key in carrito:
                    if action == "increment":
                        if carrito[pedido_key] < 5:
                            carrito[pedido_key] += 1
                    elif action == "decrement":
                        if carrito[pedido_key] > 1:
                            carrito[pedido_key] -= 1
                        else:
                            carrito.pop(pedido_key)
                request.session['carrito'] = carrito
                request.session.modified = True
                cantidad = carrito[pedido_key] if pedido_key in carrito else 0
            
            total_processor = carrito_total(request)
            return Response({
                'total_precio':total_processor['total_precio'],
                'total_productos':total_processor['total_productos'],
                'cantidad':cantidad,
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EliminarPedidoView(APIView):
    permission_classes = [TieneCarrito,BloquearSiMantenimiento]
    throttle_classes = [CarritoThrottle]
    def post(self,request):
        serializer = EliminarPedidoSerializer(data=request.data)
        if serializer.is_valid():

            data = serializer.validated_data
            pedido_id = data['pedido_id']

            if request.user.is_authenticated:
                carrito = get_object_or_404(Carrito,usuario=request.user)
                pedido = get_object_or_404(Pedido,id=pedido_id,carrito=carrito)
                pedido.delete()
            else:
                carrito = request.session.get('carrito',{})
                if str(pedido_id) in carrito:
                    carrito.pop(str(pedido_id))
                    request.session['carrito'] = carrito

            total_processor = carrito_total(request)
            return Response({
                'total_precio':total_processor['total_precio'],
                'total_productos':total_processor['total_productos']
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AgregarAlCarritoView(APIView):
    permission_classes = [BloquearSiMantenimiento]
    throttle_classes = [CarritoThrottle]
    def post(self,request):
        serializer = AgregarAlCarritoSerializer(data=request.data)
        if serializer.is_valid():

            data = serializer.validated_data

            producto = get_object_or_404(Producto, id=data['producto_id'])
            cantidad = data['cantidad']

            if request.user.is_authenticated:
                carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
                #* Creacion de 'Pedido'
                pedido = carrito.agregar_producto(producto, cantidad)
                cantidad = pedido.cantidad
                subtotal = pedido.get_total_precio()
            else:
                carrito = request.session.get('carrito',{})
                carrito[str(data['producto_id'])] = carrito.get(str(data['producto_id']),0) + cantidad
                if carrito[str(data['producto_id'])] > 5:
                    carrito[str(data['producto_id'])] = 5
                cantidad = carrito[str(data['producto_id'])]
                request.session['carrito'] = carrito

            subtotal = producto.precio * cantidad

            total_processor = carrito_total(request)
            imagen_url = (
                producto.imagenes.first().imagen.url
                if producto.imagenes.first()
                else static('img/prod_default.webp')
            )
            return Response({
                'total_precio':total_processor['total_precio'],
                'total_productos':total_processor['total_productos'],
                'productoNombre':producto.nombre,
                'imagen_url':imagen_url,
                'cantidad_pedido':cantidad,
                'subtotal':subtotal
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class CalcularPedidoView(APIView):
    permission_classes = [TieneCarrito,BloquearSiMantenimiento]
    throttle_classes = [CalcularPedidoThrottle]
    def post(self, request):

        serializer = CalcularPedidoSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            total_processor = float(carrito_total(request).get('total_precio'))

            if data['metodo_pago'] == 'mercado_pago':

                total_compra = round(total_processor/0.923891,2)
                adicional = round(total_compra - total_processor,2)

                request.session['adicional_mp'] = adicional
                request.session.modified = True

                productos = {}
                
                if request.user.is_authenticated:
                    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
                    carrito_id = carrito.id
                    for pedido in carrito.pedidos.all():
                        productos[str(pedido.producto.id)] = pedido.get_cantidad()
                    usuario = {'user':request.user.email}
                else:
                    carrito = request.session['carrito']
                    productos = carrito
                    carrito_id = request.session['anon_cart_id']
                    usuario = {'session':request.session.session_key}

                direccion = data['calle']
                match = re.match(r'^(.*?)(?:\s+(\d+))?$', direccion.strip())
                if match:
                    calle_nombre = match.group(1).strip()
                    calle_altura = match.group(2) if match.group(2) else ''

                dni_cuit = data['dni_cuit']
                ident_type = "DNI" if data['tipo_factura'] == 'B' else 'CUIT'
                email = data['email']
                nombre = data['nombre']
                apellido = data['apellido']
                codigo_postal = data['codigo_postal']
                razon_social = data.get('razon_social','')
                tipo_factura = data.get('tipo_factura','')
                telefono = data.get('telefono', '')
                recibir_mail = data.get('recibir_mail')

                try:
                    preference = preference_mp(total_compra,carrito_id,dni_cuit,ident_type,email,nombre,apellido,codigo_postal,calle_nombre,calle_altura,razon_social,tipo_factura,telefono,recibir_mail,productos,usuario)
                    init_point = preference.get("init_point", "")
                except ValueError as e:
                    return Response({'error': str(e)}, status=500)

            else:
                total_compra = total_processor
                adicional = 0
                init_point = ''
                if request.session.get('adicional_mp',{}):
                    del request.session['adicional_mp']
                    request.session.modified = True

            if total_processor <= 0:
                return Response({'error': 'El carrito está vacío'}, status=400)
            
            return Response({
                'total': total_compra,
                'adicional': adicional,
                'init_point': init_point,
                'metodoPagoSeleccionado':data['metodo_pago'],
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Create your views here.
# ----- Preferencias de MP ----- #

def preference_mp(numero, carrito_id, dni_cuit, ident_type, email,nombre,apellido,codigo_postal,calle_nombre,calle_altura,razon_social,tipo_factura,telefono,recibir_mail,productos,usuario):
    site_url = f'{settings.MY_NGROK_URL}'

    argentina_tz = pytz.timezone('America/Argentina/Buenos_Aires')

    expiration_from = timezone.now().astimezone(argentina_tz).isoformat()
    expiration_to = (timezone.now() + timedelta(minutes=30)).astimezone(argentina_tz).isoformat()

    preference_data = {
        "items": [
            {
                "id": f"carrito-{carrito_id}",
                "title": "Compra en Twinstore",
                "description": "Productos electrónicos - Twinstore.com.ar",
                "quantity": 1,
                "currency_id": "ARS",
                "unit_price": float(numero),
                "category_id": "electronics"
            }
        ],
        "payer": {
            "name": nombre,
            "surname": apellido,
            "email": email,
            "identification": {
                "type": ident_type,
                "number": dni_cuit
            },
            "address": {
                "zip_code": codigo_postal,
                "street_name": calle_nombre,
                "street_number": calle_altura
            }
        },
        "back_urls": {
            "success": f"https://{site_url}/payment/success/",
            "failure": f"https://{site_url}/payment/failure/",
            "pending": f"https://{site_url}/payment/pendings/"
        },
        "auto_return": "approved",
        "notification_url": f"https://{site_url}/payment/webhook/",
        "statement_descriptor": "TWINSTORE",
        "external_reference": str(carrito_id),
        "expires": True,
        "expiration_date_from": expiration_from,
        "expiration_date_to": expiration_to,
        "metadata": {
            "dni_cuit": dni_cuit,
            "email": email,
            "nombre": nombre,
            "apellido": apellido,
            "codigo_postal": codigo_postal,
            "calle": f"{calle_nombre} {calle_altura}",
            "razon_social":razon_social,
            "tipo_factura":tipo_factura,
            "telefono":telefono,
            "recibir_mail":recibir_mail,
            "productos":productos,
            "usuario":usuario,
            "carrito_id":carrito_id
        },
    }
    print("Preferencia de Mercado Pago:", preference_data)

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response.get("response", {})
        init_point = preference.get("init_point")

        if not init_point or not init_point.startswith("https://www.mercadopago.com"):
            raise ValueError("Init point inválido o no generado")
        
        return preference

    except Exception as e:
        raise ValueError(f"Error al generar preferencia de pago: {str(e)}")

# ----- Realizar pedido -----#
@bloquear_si_mantenimiento
@requiere_carrito
def realizar_pedido(request):
    if request.method == "POST":
        form = UsuarioForm(request.POST)
        if not form.is_valid():
            return render(request, 'cart/realizar_pedido.html', {
                'form': form,
                'carrito': _obtener_carrito(request),
            })
        else:
            data = form.cleaned_data
            forma_pago = request.POST.get('forma_pago')

            if forma_pago not in ['efectivo', 'transferencia']:
                return redirect("core:home")
            elif forma_pago == 'transferencia':
                merchant_order_id = _generar_identificador_unico('T')
                status = 'pendiente'
            else:
                merchant_order_id = _generar_identificador_unico('E')
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
                    perfil.ciudad = data['ciudad']
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
                ciudad=data['ciudad'],
                calle_detail=data['calle_detail'],
            )

            return redirect(f"{reverse('payment:success')}?merchant_order_id={merchant_order_id}")
    else:
        if request.user.is_authenticated:
            perfil, create = PerfilUsuario.objects.get_or_create(user = request.user)
            form = UsuarioForm(initial={
                    'tipo_factura': perfil.tipo_factura,
                    'dni_cuit': perfil.dni_cuit,
                    'razon_social': perfil.razon_social,
                    'nombre': perfil.nombre,
                    'apellido': perfil.apellido,
                    'calle': perfil.calle,
                    'calle_detail': perfil.calle_detail,
                    'ciudad': perfil.ciudad,
                    'provincia': perfil.provincia,
                    'codigo_postal': perfil.codigo_postal,
                    'email': request.user.email,
                    'telefono': perfil.telefono,
                    'guardar_datos': perfil.guardar_datos
                })
        else:
            form = UsuarioForm()
        return render(request, 'cart/realizar_pedido.html', {
            'carrito': _obtener_carrito(request),
            'form':form,
            })

def _generar_identificador_pago(letra):
    fecha = datetime.now().strftime('%d%m%y')
    sufijo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{letra}-{fecha}-{sufijo}"

def _generar_identificador_unico(letra):
    while True:
        nuevo_id = _generar_identificador_pago(letra)
        if not HistorialCompras.objects.filter(merchant_order_id=nuevo_id).exists():
            return nuevo_id

def _obtener_carrito(request):
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        return carrito
    else:
        if 'anon_cart_id' not in request.session:
            request.session['anon_cart_id'] = f"anon-{uuid.uuid4()}"
        carrito_session = request.session.get('carrito',{})
        carrito = []
        for producto_id,cantidad in carrito_session.items():
            producto = get_object_or_404(Producto,id=int(producto_id))
            carrito.append({
                'id':producto.id,
                'producto':producto,
                'cantidad':cantidad,
                'total_precio':producto.precio*cantidad,
                })
        return carrito

# ----- Ver el carro -----#
def ver_carrito(request):
    #step Si esta autenticado
    carrito = _obtener_carrito(request)
    try:
        empty = False if carrito.pedidos.all() else True
    except:
        empty = False if carrito else True
    return render(request,'cart/ver_carrito.html',{
        'carrito':carrito,
        'empty':empty
        })

@requiere_carrito
def generar_presupuesto(request):
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        total_compra = float(carrito.get_total())
    else:
        carrito_session = request.session.get('carrito',{})
        carrito = []
        for producto_id,cantidad in carrito_session.items():
            producto = get_object_or_404(Producto,id=int(producto_id))
            carrito.append({
                'producto':producto,
                'cantidad':cantidad,
                'total_precio':producto.precio*cantidad,
            })
        total_compra = float(sum(item['total_precio'] for item in carrito))

    adicional = "0,00"
    if request.session.get('adicional_mp',{}):
        adicional = request.session['adicional_mp']
        total_compra += float(adicional)

    logo_path = os.path.join(settings.BASE_DIR, 'static/img/mail.webp')

    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode("utf-8")


    context = {'carrito':carrito,'fecha':datetime.date.today(),'logo_base64': logo_base64,'total_compra':total_compra,'adicional':adicional}
    html_string = render_to_string("presupuesto.html", context)
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=presupuesto.pdf"
    return response