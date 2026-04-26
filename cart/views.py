from django.http import HttpRequest
from django.shortcuts import render
from django.core import signing


from core.permissions import BloquearSiMantenimiento
from core.throttling import CarritoThrottle
from core.utils import get_configuracion_tienda

from payment.templatetags.custom_filters import formato_pesos

from .utils import (
    obtener_carrito,
    obtener_total,
    clear_carrito_cache,
    sumar_carrito,
    eliminar_del_carrito,
    actualizar_carrito,
    )

from .context_processors import carrito_total
from .permissions import TieneCarrito
from .serializers import (
    AgregarAlCarritoSerializer,
    EliminarPedidoSerializer,
    ActualizarPedidoSerializer,
)

from rest_framework.views import APIView
from rest_framework.response import Response

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