from django.http import HttpRequest
from django.shortcuts import get_object_or_404,render
from django.conf import settings
from django.core import signing
from django.core.cache import cache

from users.decorators import login_required_modal

from core.permissions import BloquearSiMantenimiento
from core.decorators import bloquear_si_mantenimiento
from core.throttling import EnviarWtapThrottle,CarritoThrottle,CalcularPedidoThrottle
from core.utils import get_configuracion_tienda

from payment.models import Cupon
from payment.templatetags.custom_filters import formato_pesos

from .utils import (
    obtener_carrito,
    obtener_total,
    clear_carrito_cache,
    crear_venta,
    obtener_crear_checkout,
    validar_compra,
    sumar_carrito,
    eliminar_del_carrito,
    actualizar_carrito,
    obtener_total_checkout
    )

from .context_processors import carrito_total
from .permissions import TieneCarrito
from .decorators import requiere_carrito
from .types import CheckoutData
from .serializers import (
    AgregarAlCarritoSerializer,
    EliminarPedidoSerializer,
    ActualizarPedidoSerializer,
    CuponSerializer,
    PagoMixtoSerializer,
    AdicionalesCheckoutSerializer,
     ValidarPagoSerializer,
    # ! DEPRECATED
    ComprobanteSerializer,
    CheckoutSerializer,
    # !
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from decimal import Decimal

LABEL_CONDICION_IVA = {
    "A": "Responsable Inscripto",
    "B": "Consumidor Final",
    "C": "Monotributista",
}

LABEL_FORMA_PAGO = {
    "efectivo": "Efectivo",
    "transferencia": "Transferencia",
    "tarjeta": "Tarjeta de crédito/débito",
    "mercado_pago": "Mercado Pago",
    "mixto": "Pago Mixto: Mercado Pago + Transferencia bancaria",
}

# ----- APIS ----- #
class ActualizarPedidoView(APIView):
    permission_classes = [TieneCarrito, BloquearSiMantenimiento]
    throttle_classes = [CarritoThrottle]

    def post(self, request:HttpRequest):
        serializer = ActualizarPedidoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        action = data["action"]
        pedido_id = signing.loads(data["pedido_id"])
        cantidad = 0

        config = get_configuracion_tienda(request)
        stock_flag = config['modo_stock'] == "estricto"
        maximo_compra = config['maximo_compra']

        cantidad = actualizar_carrito(request,pedido_id,action,stock_flag,maximo_compra)
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
        eliminar_del_carrito(request,pedido_id)

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

        producto = data['producto_obj']
        variante = data.get('variante_obj',None)
        
        config = get_configuracion_tienda(request)
        if config['modo_stock'] == 'libre':
            stock_disponible = config['maximo_compra']
        else:
            obj = variante if variante else producto
            stock_disponible = obj.obtener_stock() 

        sumar_carrito(
            request=request,
            producto=producto,
            stock_maximo=stock_disponible,
            variante=variante
        )
        clear_carrito_cache(request)

        total_processor = carrito_total(request)

        return Response({
            'totalProds': total_processor['total_productos'],
        })

class ValidarCuponView(APIView):
    permission_classes = [TieneCarrito,BloquearSiMantenimiento]
    throttle_classes = [CalcularPedidoThrottle]
    def post(self,request:HttpRequest):
        serializer = CuponSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=400)
        
        codigo = serializer.validated_data.get("codigo").upper()
        if request.session.get('checkout',{}).get('cupon',None):
            del request.session['checkout']['cupon']
            request.session.modified = True

        try:
            cupon = Cupon.objects.get(codigo=codigo)
            checkout_data:CheckoutData = request.session.get('checkout',{})
            checkout_data['cupon'] = {
                "codigo": cupon.codigo,
                "descuento": str(cupon.descuento)
            }
            request.session['checkout'] = checkout_data
            request.session.modified = True

            print(obtener_total_checkout(request))
            precio_total,_,_,cupon,_,_ = obtener_total_checkout(request)

            return Response({"precio_total": formato_pesos(precio_total),"descuento": f"-{formato_pesos(cupon)}"},status=200)
        
        except Cupon.DoesNotExist:
            if request.session.get('cupon',''):
                del request.session['cupon']
                request.session.modified = True

            return Response({"error": "Cupón inválido o inactivo."}, status=404)

# ! DEPRECATED
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

# ----- Validar datos de facturación ----- #
class ValidarFacturacionView(APIView):
    permission_classes = [BloquearSiMantenimiento,IsAuthenticated]
    def post(self, request:HttpRequest):
        serializer = CheckoutSerializer(data=request.data)
        if serializer.is_valid():
            checkout_data = request.session.get('checkout',{})
            checkout_data['facturacion'] = serializer.validated_data
            request.session['checkout'] = checkout_data
            request.session.modified = True
            label_condicion = LABEL_CONDICION_IVA.get(serializer.validated_data.get('condicion_iva',''),'')
            return Response(status=status.HTTP_200_OK,data={
                "nombre_completo":f"{serializer.validated_data['nombre']} {serializer.validated_data['apellido']}",
                "dni_cuit":serializer.validated_data['dni_cuit'],
                "condicion_iva":label_condicion,
                "direccion":f"{serializer.validated_data['direccion']}, {serializer.validated_data['localidad']}, {serializer.validated_data['codigo_postal']}",
                })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ----- Validar forma de pago ----- #
class ValidarFormaPagoView(APIView):
    def post(self,request:HttpRequest):
        serializer = ValidarPagoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=400)
        
        data = serializer.validated_data
        forma_de_pago = data.get('forma_de_pago')

        checkout:CheckoutData = request.session.get('checkout',{})
        if checkout.get('pago',{}):
            del request.session['checkout']['pago']
            request.session.modified = True

        pago_data = {
            'forma_de_pago': forma_de_pago,
            'es_mixto': False
        }

        if forma_de_pago == 'mixto':
            # * Validar monto mixto
            precio_total, _, _ = obtener_total(obtener_carrito(request))
            monto_mixto = data.get('monto_mixto')
            if monto_mixto is None or monto_mixto <= 0:
                return Response({"error": "Monto mixto inválido.","mixto": True}, status=400)
            if monto_mixto >= (precio_total*Decimal('0.95')):
                return Response({"error": "El monto mixto no puede ser mayor o igual al 95% del total.","mixto": True}, status=400)
            
            pago_data['es_mixto'] = True
            pago_data['monto_transferencia'] = str(monto_mixto)

        checkout['pago'] = pago_data
        request.session['checkout'] = checkout
        request.session.modified = True

        precio_total, adicional, _, _, monto_mercadopago, monto_transferencia = obtener_total_checkout(request)

        return Response(
                {
                    "pago_total": formato_pesos(precio_total),
                    "monto_transferencia": formato_pesos(monto_transferencia) if monto_transferencia else None,
                    "monto_mercadopago": formato_pesos(monto_mercadopago) if monto_mercadopago else None,
                    "adicional": formato_pesos(adicional) if adicional else None,
                    "mixto": pago_data['es_mixto'],
                    "title": LABEL_FORMA_PAGO.get(forma_de_pago,''),
                    "forma_de_pago": forma_de_pago,
                },
                status=200
            )

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
        
        carrito = obtener_carrito(request)
        config = get_configuracion_tienda(request)
        if not validar_compra(carrito,request,config):
            return Response({"reload": True},status=400)
        
        data_checkout = checkout_serializer.validated_data
        data_comprobante = comprobante_serializer.validated_data

        order_id,init_point = crear_venta(carrito, request, data_checkout,forma_pago.validated_data.get('forma_de_pago'),data_comprobante.get('comprobante'))

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
# ----- Finalizar pedido -----#
@login_required_modal
@requiere_carrito
@bloquear_si_mantenimiento
def finalizar_compra(request: HttpRequest):
    checkout = request.session.get('checkout',{})
    if checkout:
        del request.session['checkout']
        request.session.modified = True

    carrito = obtener_carrito(request)
    precio_total,precio_subtotal,descuento = obtener_total(carrito)
    return render(request, 'cart/checkout.html',{
        'carrito':carrito,
        'precio_total':precio_total,
        'precio_subtotal':precio_subtotal,
        'descuento':descuento,
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