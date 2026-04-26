from django.shortcuts import render,get_object_or_404,redirect
from django.contrib import messages
from django.core.signing import BadSignature
from django.core import signing
from django.http import HttpRequest

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from users.decorators import login_required_modal

from core.permissions import BloquearSiMantenimiento
from core.decorators import bloquear_si_mantenimiento

from payment.models import Cupon
from payment.templatetags.custom_filters import formato_pesos

from cart.decorators import requiere_carrito

from .types import CheckoutData
from .models import Venta,EstadoPedido
from .serializers import (
    IntSigned,
    CuponSerializer,
    ValidarPagoSerializer,
    CheckoutSerializer,
)
from .utils import (
    obtener_carrito,
    obtener_total,
    obtener_total_checkout,
    finalizar_checkout
    )

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
# Create your views here.
class ArrepentimientoPostView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request: HttpRequest):
        serializer = IntSigned(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=400)
        venta_signed = serializer.validated_data.get('numero_firmado')
        try:
            venta_id = signing.loads(venta_signed)
        except BadSignature:
            return Response({'error':'Firma inválida'},status=400)
        
        venta = get_object_or_404(Venta,id=venta_id,usuario=request.user)
        if not venta.verificar_arrepentimiento():
            return Response({'error':'No se puede solicitar el arrepentimiento'},status=400)
        
        venta.estado = 'arrepentido'
        venta.requiere_revision = True
        EstadoPedido.objects.get_or_create(
            venta=venta,
            estado="Arrepentimiento (Servidor)",
            defaults={
                "comentario": "Arrepentimiento solicitado por el cliente"
            }
        )
        venta.save()

        messages.success(request,'Arrepentimiento solicitado con éxito')

        return Response({'reload':True},status=200)
    
class ValidarCuponView(APIView):
    permission_classes = [IsAuthenticated]
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

class FinalizarCompraView(APIView):
    def post(self,request:HttpRequest):
        ... # * Este endpoint se encarga de finalizar la compra, creando la orden y redirigiendo al usuario al medio de pago correspondiente (Ej: Mercado Pago)
        resultado = finalizar_checkout(request)
        print(resultado)
        return Response(resultado)

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
    return render(request, 'orders/finalizar_compra.html',{
        'carrito':carrito,
        'precio_total':precio_total,
        'precio_subtotal':precio_subtotal,
        'descuento':descuento,
        })

@login_required_modal
def pedido_exitoso(request: HttpRequest,merchant_order_id:int):
    venta = get_object_or_404(Venta,merchant_order_id=merchant_order_id)
    if request.user != venta.usuario:
        messages.error(request,'No tienes permiso para ver este pedido')
        return redirect('core:home')
    return render(request,'orders/pedido_exitoso.html',{
        'venta': venta
    })