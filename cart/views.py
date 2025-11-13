from django.http import HttpRequest
from django.shortcuts import get_object_or_404,render
from django.conf import settings
from django.core import signing

from users.decorators import login_required_modal

from core.permissions import BloquearSiMantenimiento
from core.decorators import bloquear_si_mantenimiento
from core.throttling import EnviarWtapThrottle,CarritoThrottle,CalcularPedidoThrottle

from payment.models import Cupon
from payment.templatetags.custom_filters import formato_pesos

from .utils import obtener_carrito,obtener_total,clear_carrito_cache,crear_historial_compras,obtener_crear_checkout
from .models import Producto, Carrito, Pedido
from products.models import ColorProducto

from .context_processors import carrito_total
from .permissions import TieneCarrito
from .decorators import requiere_carrito
from .serializers import (
    AgregarAlCarritoSerializer,
    EliminarPedidoSerializer,
    ActualizarPedidoSerializer,
    CuponSerializer,
    PagoMixtoSerializer,
    CheckoutSerializer,
    AdicionalesCheckoutSerializer,
    ComprobanteSerializer
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from decimal import Decimal

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
    permission_classes = [TieneCarrito, BloquearSiMantenimiento]
    throttle_classes = [CarritoThrottle]

    def post(self, request):
        serializer = ActualizarPedidoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        action = data["action"]
        pedido_id = signing.loads(data["pedido_id"])
        cantidad = 0

        if request.user.is_authenticated:
            pedido = Pedido.objects.filter(
                id=pedido_id, carrito__usuario=request.user
            ).select_related("producto").first()

            if not pedido:
                return Response({"error": "Pedido no encontrado"}, status=404)

            if action == "mas" and pedido.cantidad < 5:
                pedido.cantidad += 1
                pedido.save(update_fields=["cantidad"])
            elif action == "menos":
                if pedido.cantidad > 1:
                    pedido.cantidad -= 1
                    pedido.save(update_fields=["cantidad"])
                else:
                    pedido.delete()
                    pedido = None

            cantidad = pedido.cantidad if pedido else 0

        else:
            carrito = request.session.get("carrito", {})
            key = str(pedido_id)
            if key in carrito:
                if action == "mas" and carrito[key] < 5:
                    carrito[key] += 1
                elif action == "menos":
                    if carrito[key] > 1:
                        carrito[key] -= 1
                    else:
                        carrito.pop(key)

            request.session["carrito"] = carrito
            request.session.modified = True
            cantidad = carrito.get(key, 0)

        clear_carrito_cache(request)

        carrito = obtener_carrito(request)
        precio_total, precio_subtotal, descuento = obtener_total(carrito)
        total_productos = carrito_total(request)

        try:
            item = next((i for i in carrito if i['id'] == pedido_id), None)
        except:
            item = None


        return Response({
            "totalPrecio": formato_pesos(precio_total),
            "subTotal": formato_pesos(precio_subtotal),
            "totalProductos": total_productos['total_productos'],
            "descuento":formato_pesos(descuento),
            "cantidad": cantidad,
            "precio":formato_pesos(item['precio']) if item else None,
            "precioAnterior":formato_pesos(item['precio_anterior']) if item else None
        })

class EliminarPedidoView(APIView):
    permission_classes = [TieneCarrito,BloquearSiMantenimiento]
    throttle_classes = [CarritoThrottle]
    def post(self,request:HttpRequest):
        serializer = EliminarPedidoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        pedido_id = signing.loads(data.get('pedido_id'))

        clear_carrito_cache(request)

        if request.user.is_authenticated:
            carrito = get_object_or_404(Carrito,usuario=request.user)
            pedido = get_object_or_404(Pedido,id=int(pedido_id),carrito=carrito)
            pedido.delete()
        else:
            carrito = request.session.get('carrito',{})
            carrito.pop(str(pedido_id), None)
            request.session['carrito'] = carrito

        total_productos = carrito_total(request)
        carrito = obtener_carrito(request)
        precio_total,precio_subtotal,descuento = obtener_total(carrito)
        return Response({
            "totalPrecio": formato_pesos(precio_total),
            "subTotal": formato_pesos(precio_subtotal),
            "totalProductos": total_productos['total_productos'],
            "descuento":formato_pesos(descuento),
            "cantidad": 0,
            "precio":None,
            "precioAnterior":None
        })

class AgregarAlCarritoView(APIView):
    permission_classes = [BloquearSiMantenimiento]
    throttle_classes = [CarritoThrottle]
    def post(self,request):
        serializer = AgregarAlCarritoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        producto_id = signing.loads(data.get('producto_id'))
        producto = get_object_or_404(Producto, id=producto_id)

        color_data = data.get('color_id')
        if color_data:
            try:
                color_id = signing.loads(color_data)
                color = get_object_or_404(ColorProducto, id=int(color_id))
            except Exception:
                color = None
        else:
            color = None

        if request.user.is_authenticated:
            carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
            carrito.agregar_producto(producto, 1 ,color)

        else:
            carrito = request.session.get('carrito', {})
            key = f"{producto_id}-{color.id if color else 'null'}"
            carrito[key] = carrito.get(key, 0) + 1
            if carrito[key] > 5:
                carrito[key] = 5
            request.session['carrito'] = carrito

        clear_carrito_cache(request)

        total_processor = carrito_total(request)

        return Response({
            'totalProds':total_processor['total_productos'],
        })

class ValidarCuponView(APIView):
    permission_classes = [TieneCarrito,BloquearSiMantenimiento]
    throttle_classes = [CalcularPedidoThrottle]
    def post(self,request):
        serializer = CuponSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=400)
        
        codigo = serializer.validated_data.get("codigo").upper()

        try:
            cupon = Cupon.objects.get(codigo=codigo)
            carrito = obtener_carrito(request)
            precio_total, _, _ = obtener_total(carrito)

            cupon_descuento = (precio_total * cupon.descuento) / 100
            total_precio = precio_total - cupon_descuento

            checkout = obtener_crear_checkout(request)
            checkout.cupon_id = cupon.id
            checkout.descuento = cupon_descuento
            checkout.save()

            return Response({'cupon': f"-{formato_pesos(cupon_descuento)}", 'total': formato_pesos(total_precio)},status=200)
        
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
        
        carrito = obtener_carrito(request)
        total_carrito, _, _ = obtener_total(carrito)
        pago_transferencia = serializer.validated_data.get('monto')

        if pago_transferencia >= total_carrito:
            return Response({"error":"El valor ingresado no es válido."},status=404)

        if pago_transferencia/total_carrito > 0.95:
            return Response({"error":f"El valor de mercado pago no puede ser menor al 5% de la compra"},status=404)
        
        pago_mp = round((total_carrito-pago_transferencia)*Decimal(settings.MERCADOPAGO_COMMISSION),2)

        adicional = pago_mp - (total_carrito - pago_transferencia)
        total = pago_mp + pago_transferencia

        checkout = obtener_crear_checkout(request)
        checkout.forma_de_pago = 'mixto'
        checkout.mixto = pago_mp
        checkout.adicional = adicional
        checkout.save()

        return Response({"mercadopago":formato_pesos(pago_mp),"adicional":formato_pesos(adicional),"total":formato_pesos(total),"transferencia":formato_pesos(pago_transferencia)},status=200)

class ValidarFacturacionView(APIView):
    permission_classes = [BloquearSiMantenimiento,IsAuthenticated]
    def post(self, request:HttpRequest):
        serializer = CheckoutSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"valid": True}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckoutView(APIView):
    permission_classes = [BloquearSiMantenimiento,IsAuthenticated]
    throttle_classes = [CalcularPedidoThrottle]
    def post(self,request:HttpRequest):
        checkout_serializer = CheckoutSerializer(data=request.data)
        comprobante_serializer = ComprobanteSerializer(data=request.data)
        forma_pago = AdicionalesCheckoutSerializer(data=request.data)

        if not comprobante_serializer.is_valid():
            return Response(comprobante_serializer.errors,status=400)
        
        if not checkout_serializer.is_valid():
            return Response(checkout_serializer.errors,status=400)
        
        if not forma_pago.is_valid():
            return Response(forma_pago.errors,status=400)
        
        data_checkout = checkout_serializer.validated_data
        data_comprobante = comprobante_serializer.validated_data

        order_id,init_point = crear_historial_compras(request, data_checkout,forma_pago.validated_data.get('forma_de_pago'),data_comprobante.get('comprobante'))

        return Response({'success':True,'order_id':order_id,'init_point':init_point if init_point else None},status=200)

class AdicionalesCheckoutView(APIView):
    permission_classes = [BloquearSiMantenimiento,IsAuthenticated]
    throttle_classes = [CalcularPedidoThrottle]
    def post(self,request:HttpRequest):
        serializer = AdicionalesCheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=400)
        
        data = serializer.validated_data
        forma_de_pago = data.get('forma_de_pago','')

        carrito = obtener_carrito(request)
        precio_total, _, _ = obtener_total(carrito)

        checkout = obtener_crear_checkout(request)

        if request.data.get('forma_de_pago') == 'mercado_pago':
            total_compra = round(precio_total*Decimal(settings.MERCADOPAGO_COMMISSION),2)
            adicional = round(total_compra - precio_total,2)
            checkout.adicional = adicional
            checkout.forma_de_pago = 'mercado_pago'
            checkout.save()

            if checkout.descuento:
                total_compra -= checkout.descuento

            return Response({
                'total': formato_pesos(total_compra),
                'adicional': formato_pesos(adicional) if adicional != 0 else None,
            })

        if forma_de_pago in ['efectivo','transferencia','tarjeta','mixto']:
            checkout.adicional = Decimal('0.00')
            checkout.forma_de_pago = forma_de_pago
            checkout.save()
            if checkout.descuento:
                precio_total -= checkout.descuento

            return Response({
                'total': formato_pesos(precio_total),
            })

# Create your views here.
# -- Preferencia MercadoPago -- #
# ----- Finalizar pedido -----#
@login_required_modal
@requiere_carrito
@bloquear_si_mantenimiento
def finalizar_compra(request: HttpRequest):
    carrito = obtener_carrito(request)
    precio_total,precio_subtotal,descuento = obtener_total(carrito)
    return render(request, 'cart/finalizar_compra.html',{
        'carrito':carrito,
        'precio_total':precio_total,
        'precio_subtotal':precio_subtotal,
        'descuento':descuento
        })

# ----- Ver el carro -----#
def ver_carrito(request):
    carrito = obtener_carrito(request)
    precio_total,precio_subtotal,descuento = obtener_total(carrito)
    return render(request,'cart/ver_carrito.html',{
        'carrito':carrito,
        'precio_total':precio_total,
        'precio_subtotal':precio_subtotal,
        'descuento':descuento
        })