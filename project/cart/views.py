from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404,render
from users.forms import UsuarioForm
from .models import Producto, Carrito, Pedido
import mercadopago
from django.conf import settings
from users.models import PerfilUsuario
from django.utils import timezone
import uuid
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CalcularPedidoSerializer,AgregarAlCarritoSerializer,EliminarPedidoSerializer,ActualizarPedidoSerializer
import re
from .context_processors import carrito_total
from .permissions import TieneCarrito
from core.permissions import BloquearSiMantenimiento
from .decorators import requiere_carrito
from django.templatetags.static import static
from django.template.loader import render_to_string
from weasyprint import HTML
import datetime
import os
import base64

from core.throttling import EnviarWtapThrottle,CarritoThrottle,CalcularPedidoThrottle

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

    argentina_tz = timezone.get_fixed_timezone(-180)

    expiration_from = timezone.localtime(timezone.now(), argentina_tz).isoformat()
    expiration_to = timezone.localtime(timezone.now() + timedelta(days=1), argentina_tz).isoformat()

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

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
    except Exception as e:
        raise ValueError(f"Error al generar preferencia de pago: {str(e)}")
    if not preference["init_point"].startswith("https://www.mercadopago.com"):
        raise ValueError("Init point inválido")
    return preference

# ----- Realizar pedido -----#
@requiere_carrito
def realizar_pedido(request):
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        perfil, create = PerfilUsuario.objects.get_or_create(user = request.user)
        form = UsuarioForm(initial={
                'tipo_factura': perfil.tipo_factura,
                'dni_cuit': perfil.dni_cuit,
                'razon_social': perfil.razon_social,
                'nombre': perfil.nombre,
                'apellido': perfil.apellido,
                'calle': perfil.calle,
                'calle_detail': perfil.calle_detail,
                'cuidad': perfil.cuidad,
                'provincia': perfil.provincia,
                'codigo_postal': perfil.codigo_postal,
                'email': request.user.email,
                'telefono': perfil.telefono,
                'guardar_datos': perfil.guardar_datos
            })
    else:
        form = UsuarioForm()
        carrito_session = request.session.get('carrito',{})
        carrito = []
        if 'anon_cart_id' not in request.session:
            request.session['anon_cart_id'] = f"anon-{uuid.uuid4()}"
        for producto_id,cantidad in carrito_session.items():
            producto = get_object_or_404(Producto,id=int(producto_id))
            carrito.append({
                'producto':producto,
                'cantidad':cantidad,
                'total_precio':producto.precio*cantidad,
                })
    return render(request, 'cart/realizar_pedido.html', {
        'carrito': carrito,
        'form':form,
        })

# ----- Ver el carro -----#
def ver_carrito(request):
    #step Si esta autenticado
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        empty = False if carrito.pedidos.all() else True
        return render(request, 'cart/ver_carrito.html', {
            'carrito': carrito,
            'empty':empty
        })
    #step Si NO! esta autenticado
    if 'anon_cart_id' not in request.session:
        request.session['anon_cart_id'] = f"anon-{uuid.uuid4()}"
    carrito_session = request.session.get('carrito',{})
    carrito = []
    for producto_id,cantidad in carrito_session.items():
        producto = get_object_or_404(Producto,id=int(producto_id))
        imagen_url = producto.imagenes.first().imagen.url if producto.imagenes.first() else 'img/prod_default.webp'
        carrito.append({
            'id':producto.id,
            'producto':producto,
            'cantidad':cantidad,
            'total_precio':producto.precio*cantidad,
            'imagen_url': imagen_url,
            })
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