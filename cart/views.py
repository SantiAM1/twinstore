from django.http import Http404, HttpResponse, HttpRequest
from django.shortcuts import redirect, get_object_or_404,render
from django.conf import settings
from django.utils import timezone
from django.templatetags.static import static
from django.template.loader import render_to_string
from django.urls import reverse
from django.core import signing
from django.core.signing import BadSignature

from users.forms import UsuarioForm,TerminosYCondiciones
from users.models import PerfilUsuario,DatosFacturacion

from core.permissions import BloquearSiMantenimiento
from core.decorators import bloquear_si_mantenimiento
from core.throttling import EnviarWtapThrottle,CarritoThrottle,CalcularPedidoThrottle

from payment.models import HistorialCompras,Cupon,EstadoPedido,PagoMixtoTicket
from payment.templatetags.custom_filters import formato_pesos

from .models import Producto, Carrito, Pedido
from products.models import ColorProducto

import mercadopago

from .serializers import CalcularPedidoSerializer,AgregarAlCarritoSerializer,EliminarPedidoSerializer,ActualizarPedidoSerializer,CuponSerializer,PagoMixtoSerializer,PagoMixtoInitSerializer
from .context_processors import carrito_total
from .permissions import TieneCarrito
from .decorators import requiere_carrito

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from decimal import Decimal
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
from datetime import date

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
                    producto_id, color_str = pedido_id.split('-') 
                    producto = Producto.objects.get(id=int(producto_id))
                    productos.append({
                        "nombre": producto.nombre,
                        "cantidad": cantidad,
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
            pedido_id = signing.loads(data.get('pedido_id'))

            if request.user.is_authenticated:
                carrito = get_object_or_404(Carrito, usuario=request.user)
                pedido = get_object_or_404(Pedido, id=int(pedido_id), carrito=carrito)
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

            total_processor = carrito_total(request,type='views',pedido=pedido if request.user.is_authenticated else pedido_key)
            return Response({
                'total_precio':formato_pesos(total_processor['total_precio']),
                'sub_total':formato_pesos(total_processor['sub_total']),
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
            pedido_id = signing.loads(data.get('pedido_id'))

            if request.user.is_authenticated:
                carrito = get_object_or_404(Carrito,usuario=request.user)
                pedido = get_object_or_404(Pedido,id=int(pedido_id),carrito=carrito)
                pedido.delete()
            else:
                carrito = request.session.get('carrito',{})
                if str(pedido_id) in carrito:
                    carrito.pop(str(pedido_id))
                    request.session['carrito'] = carrito

            total_processor = carrito_total(request)
            return Response({
                'total_precio':formato_pesos(total_processor['total_precio']),
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
            producto_id = signing.loads(data.get('producto_id'))
            producto = get_object_or_404(Producto, id=producto_id)
            cantidad = data['cantidad']
            if data.get('color'):
                color_id = signing.loads(data.get('color'))
                color = get_object_or_404(ColorProducto,id=color_id)
            else:
                color = None

            if request.user.is_authenticated:
                carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
                #* Creacion de 'Pedido'
                pedido = carrito.agregar_producto(producto, cantidad,color)
                cantidad = pedido.cantidad
                subtotal = pedido.get_total_precio()
                nombre_producto = pedido.get_nombre_producto()
            else:
                carrito = request.session.get('carrito', {})
                key = f"{producto_id}-{color.id if color else 'null'}"
                print(key)
                carrito[key] = carrito.get(key, 0) + cantidad
                if carrito[key] > 5:
                    carrito[key] = 5
                cantidad = carrito[key]
                request.session['carrito'] = carrito
                nombre_producto = f"({color.nombre}) {producto.nombre}" if color else producto.nombre
                
            subtotal = producto.precio * cantidad

            total_processor = carrito_total(request)
            imagen_url = producto.portada.url if producto.portada else static('img/prod_default.webp'
            )
            return Response({
                'total_precio':formato_pesos(total_processor['total_precio']),
                'total_productos':total_processor['total_productos'],
                'productoNombre':nombre_producto,
                'imagen_url':imagen_url,
                'cantidad_pedido':cantidad,
                'subtotal':formato_pesos(subtotal)
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

            processor = carrito_total(request,type="api")
            total_processor = float(processor['total_precio'])
            
            if data['metodo_pago'] == 'mercado_pago':

                total_compra = round(total_processor*settings.MERCADOPAGO_COMMISSION,2)
                adicional = round(total_compra - total_processor,2)

                request.session['adicional_mp'] = adicional
                request.session.modified = True

                productos = {}
                
                if request.user.is_authenticated:
                    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
                    carrito_id = carrito.id
                    for pedido in carrito.pedidos.all():
                        productos[str(pedido.dict_type())] = pedido.get_cantidad()
                    usuario = {'id':request.user.id}
                else:
                    carrito = request.session['carrito']
                    productos = carrito
                    carrito_id = request.session['anon_cart_id']
                    usuario = {'key':request.session.session_key}

                direccion = data['calle']
                match = re.match(r'^(.*?)(?:\s+(\d+))?$', direccion.strip())
                if match:
                    calle_nombre = match.group(1).strip()
                    calle_altura = match.group(2) if match.group(2) else ''

                dni_cuit = data['dni_cuit']
                ident_type = "DNI" if data['condicion_iva'] == 'B' else 'CUIT'
                email = data['email']
                nombre = data['nombre']
                apellido = data['apellido']
                codigo_postal = data['codigo_postal']
                razon_social = data.get('razon_social','')
                condicion_iva = data.get('condicion_iva','')
                telefono = data.get('telefono', '')
                recibir_mail = data.get('recibir_mail')

                metadata = {
                    "dni_cuit": dni_cuit,
                    "email": email,
                    "nombre": nombre,
                    "apellido": apellido,
                    "codigo_postal": codigo_postal,
                    "calle": f"{calle_nombre} {calle_altura}",
                    "razon_social":razon_social,
                    "condicion_iva":condicion_iva,
                    "telefono":telefono,
                    "recibir_mail":recibir_mail,
                    "productos":productos,
                    'usuario':usuario,
                }

                if request.session.get('cupon',''):
                    cupon = request.session.get('cupon').get('id')
                    metadata['cupon'] = cupon

                firma = {"firma":signing.dumps(metadata)}

                try:
                    preference = preference_mp(total_compra,carrito_id,dni_cuit,ident_type,email,nombre,apellido,codigo_postal,calle_nombre,calle_altura,firma)
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
                'total': formato_pesos(total_compra),
                'adicional': formato_pesos(adicional) if adicional != 0 else '$0,00',
                'init_point': init_point,
                'metodoPagoSeleccionado':data['metodo_pago'],
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ValidarCuponView(APIView):
    permission_classes = [TieneCarrito,BloquearSiMantenimiento]
    throttle_classes = [CalcularPedidoThrottle]
    def post(self,request):
        serializer = CuponSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=400)
        
        codigo = serializer.validated_data.get("codigo").upper()

        try:
            cupon = Cupon.objects.get(codigo=codigo, activo=True)
            request.session['cupon'] = {"descuento":float(cupon.descuento),"id":int(cupon.id)}
            processor = carrito_total(request,type="api")

            return Response({
                "porcentaje": float(cupon.descuento),
                "descuento":formato_pesos(processor['descuento']),
                "nuevo_total":formato_pesos(processor['total_precio'])
            })
        
        except Cupon.DoesNotExist:
            if request.session.get('cupon',''):
                del request.session['cupon']
                request.session.modified = True

            return Response({"error": "Cupón inválido o inactivo."}, status=404)

class ValidarPagoMixtoView(APIView):
    permission_classes = [TieneCarrito,BloquearSiMantenimiento]
    throttle_classes = [CalcularPedidoThrottle]
    def post(self,request):
        serializer = PagoMixtoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=400)
        
        total_carrito = carrito_total(request,type="api").get('total_precio')
        pago_transferencia = serializer.validated_data.get('numero')

        if pago_transferencia >= total_carrito:
            return Response({"error":"El valor ingresado no es válido."},status=404)

        if pago_transferencia/total_carrito > 0.95:
            return Response({"error":f"El valor de mercado pago no puede ser menor al 5% de la compra"},status=404)
        
        pago_mp = round((total_carrito-pago_transferencia)*Decimal(settings.MERCADOPAGO_COMMISSION),2)

        request.session['pago-mixto'] = {
            'transferencia':float(pago_transferencia),
            'mercadopago':float(pago_mp)
        }

        return Response({"mercadopago":float(pago_mp)},status=200)

class PagoMixtoInitPointMPView(APIView):
    permission_classes = [BloquearSiMantenimiento]
    throttle_classes = [CalcularPedidoThrottle]
    def post(self,request):
        serializer = PagoMixtoInitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=400)
        
        numero_firmado = serializer.validated_data.get('numero_firmado')

        try:
            ticket_id = signing.loads(numero_firmado)
        except BadSignature:
            return Response({'error': 'Firma inválida'}, status=400)

        try:
            ticket = PagoMixtoTicket.objects.get(id=ticket_id)
            if ticket.tipo != 'mercadopago' or ticket.estado == 'aprobado':
                return Response(status=400)
            data = ticket.get_preference_data()
            metadata = data.get('metadata')
            firma = {"firma":signing.dumps(metadata)}

            try:
                preference = preference_mp(data['numero'],data['ticket_id'],data['dni_cuit'],data['ident_type'],data['email'],data['nombre'],data['apellido'],data['codigo_postal'],data['calle_nombre'],data['calle_altura'],firma,backurl=data['backurl'])
                init_point = preference.get("init_point", "")
                return Response({'init_point':init_point},status=200)
            except ValueError as e:
                return Response({'error': str(e)}, status=500)
            
        except PagoMixtoTicket.DoesNotExist:
            return Response(status=404)


# Create your views here.
# ----- Preferencias de MP ----- #

def preference_mp(numero, carrito_id, dni_cuit, ident_type, email,nombre,apellido,codigo_postal,calle_nombre,calle_altura,firma,backurl="payment/success/"):
    site_url = f'{settings.SITE_URL}'

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
            "success": f"https://{site_url}/{backurl}",
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
        "metadata": firma,
        "binary_mode": True,
    }

    print(preference_data)

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
        terms = TerminosYCondiciones(request.POST)
        form = UsuarioForm(request.POST)
        if not (form.is_valid() and terms.is_valid()):
            return render(request, 'cart/realizar_pedido.html', {
                'form': form,
                'terms':terms,
                'carrito': _obtener_carrito(request),
            })
        else:
            data = form.cleaned_data
            forma_pago = request.POST.get('forma_pago')

            if forma_pago not in ['efectivo', 'transferencia','mixto']:
                raise Http404("Medios de pago no válidos")
            
            total_carrito = carrito_total(request,type="api").get('total_precio')

            if forma_pago == 'mixto':
                merchant_order_id = _generar_identificador_unico('M')
                status = 'pendiente'
                pago_mixto = request.session.get('pago-mixto','')
                if not pago_mixto:
                    raise Http404("Petición incompleta")
                total_carrito = pago_mixto['transferencia'] + pago_mixto['mercadopago']
                del request.session['pago-mixto']
                request.session.modified = True
                
            elif forma_pago == 'transferencia':
                merchant_order_id = _generar_identificador_unico('T')
                status = 'pendiente'
            else:
                merchant_order_id = _generar_identificador_unico('E')
                status = 'confirmado'

            if request.user.is_authenticated:
                carrito = get_object_or_404(Carrito, usuario=request.user)

                # * Armamos el detalle de productos
                productos = []
                for pedido in carrito.pedidos.all():
                    productos.append({
                        'sku': pedido.producto.sku,
                        'nombre': pedido.get_nombre_producto(),
                        'precio_unitario': float(pedido.producto.precio),
                        'cantidad': pedido.cantidad,
                        'subtotal': float(pedido.get_total_precio()),
                        'proveedor':pedido.producto.proveedor
                    })

                # * Borramos el carrito y pedidos
                carrito.pedidos.all().delete()
                carrito.delete()

            else:
                carrito = request.session['carrito']
                if not carrito:
                    raise Http404("Carrito vacio")
                
                productos = []
                for producto_id,cantidad in carrito.items():
                    producto_id_str, color_str = producto_id.split('-') 
                    if color_str != 'null':
                        color = get_object_or_404(ColorProducto, id=int(color_str))
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

            if forma_pago == 'mixto':

                PagoMixtoTicket.objects.create(
                    historial=historial,
                    monto=pago_mixto['transferencia'],
                    tipo='transferencia'
                )
                PagoMixtoTicket.objects.create(
                    historial=historial,
                    monto=pago_mixto['mercadopago'],
                    tipo='mercadopago'
                )

            if request.session.get('cupon',''):
                cupon_id = request.session['cupon'].get('id')
                try:
                    cupon = Cupon.objects.get(id=int(cupon_id))
                    EstadoPedido.objects.create(
                        historial=historial,
                        estado="Cupón Aplicado (Servidor)",
                        comentario=f"Cupón CÓDIGO #{cupon.codigo} del %{cupon.descuento} Aplicado en la compra"
                    )
                    cupon.delete()
                except Cupon.DoesNotExist:
                    EstadoPedido.objects.create(
                        historial=historial,
                        estado="Cupón Duplicado! (Servidor)",
                        comentario=f"El cupón ingresado no fue encontrado. \nAccion requerida: RECHAZAR el historial y contactar con el cliente."
                    )

            DatosFacturacion.objects.create(
                historial=historial,
                nombre=data['nombre'],
                apellido=data['apellido'],
                razon_social=data['razon_social'],
                dni_cuit=data['dni_cuit'],
                condicion_iva=data['condicion_iva'],
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
                    'condicion_iva': perfil.condicion_iva,
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
                })
        else:
            form = UsuarioForm()
        terms = TerminosYCondiciones()
        carrito = _obtener_carrito(request)
        if not carrito:
            return redirect('core:home')

        return render(request, 'cart/realizar_pedido.html', {
                'carrito': carrito,
                'form': form,
                'terms':terms
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
        pedidos_validos = []
        for pedido in carrito.pedidos.all():
            if pedido.producto.inhabilitar:
                pedido.delete()
            else:
                pedidos_validos.append(pedido)
        return carrito if pedidos_validos else None
    else:
        if 'anon_cart_id' not in request.session:
            request.session['anon_cart_id'] = f"anon-{uuid.uuid4()}"
        carrito_session = request.session.get('carrito', {})
        carrito = []
        for producto_id, cantidad in carrito_session.items():
            producto_id_str, color_id_str = producto_id.split('-')
            producto_id = int(producto_id_str)
            if color_id_str != 'null':
                color = get_object_or_404(ColorProducto, id=int(color_id_str))
            producto = get_object_or_404(Producto, id=producto_id)
            nombre_producto = f"({color.nombre}) {producto.nombre}" if color_id_str != 'null' else producto.nombre
            if not producto.inhabilitar:
                carrito.append({
                    'id': f"{producto.id}-{color_id_str}",
                    'producto': producto,
                    'cantidad': cantidad,
                    'total_precio': producto.precio * cantidad,
                    'nombre_producto':nombre_producto
                })
        return carrito if carrito else None

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
    carrito = _obtener_carrito(request)
    if request.user.is_authenticated:
        total_compra = float(carrito.get_total())
    else:
        total_compra = float(sum(item['total_precio'] for item in carrito))

    adicional = "0,00"
    if request.session.get('adicional_mp',{}):
        adicional = request.session['adicional_mp']
        total_compra += float(adicional)

    logo_path = os.path.join(settings.BASE_DIR, 'static/img/mail.webp')

    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode("utf-8")


    context = {'carrito':carrito,'fecha':date.today(),'logo_base64': logo_base64,'total_compra':total_compra,'adicional':adicional}
    html_string = render_to_string("presupuesto.html", context)
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=presupuesto.pdf"
    return response