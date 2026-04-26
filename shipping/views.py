from .serializers import EnvioSerializer,ObtenerSucursalesSerializer,ValidarEnvioSerializer
from .models import ShippingConfig
from .services.zipnova import ZipnovaService

from rest_framework.views import APIView
from rest_framework.response import Response
from django.template.loader import render_to_string
from django.http import HttpRequest

from cart.utils import obtener_carrito
from orders.utils import obtener_total_checkout

from payment.templatetags.custom_filters import formato_pesos,fecha_humana

# Create your views here.
class CotizarEnvioAPI(APIView):
    def post(self, request: HttpRequest):
        serializer = EnvioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipping_config = ShippingConfig.objects.first()

        if not shipping_config:
            return Response({"message": "La tienda no tiene configurado ShippingConfig."},status=400)

        data = serializer.validated_data

        service = ZipnovaService(shipping_config)
        carrito = obtener_carrito(request)
        destino = {
            'cuidad': data['localidad_cotiza'],
            'estado': data['provincia_cotiza'],
            'codigo_postal': data['codigo_postal_cotiza']
        }
        cotizacion = service.cotizar(carrito, destino)
        html = render_to_string('orders/partials/empresas.html',{'empresas':cotizacion})

        checkout_data = request.session.get('checkout',{})
        checkout_data['shipping'] = cotizacion
        request.session['checkout'] = checkout_data
        request.session.modified = True

        return Response({"html":html},status=200)

class ObtenerSucursalesAPI(APIView):
    def post(self, request: HttpRequest):
        serializer = ObtenerSucursalesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        checkout_data = request.session.get('checkout',{})

        shipping_session = checkout_data.get('shipping',[])
        if not shipping_session:
            return Response(status=400)

        item_encontrado = next(
            (item for item in shipping_session if 
            item["carrier_name"] == data["carrier_name"]  and 
            item["service_code"] == data["service_code"]), 
            None
        )

        if not item_encontrado:
            return Response(status=400)
    
    
        html = render_to_string('orders/partials/sucursales.html',{'sucursales':item_encontrado.get('sucursales',[])})

        return Response({"html":html},status=200)
    
class ValidarEnvioAPI(APIView):
    def post(self, request: HttpRequest):
        serializer = ValidarEnvioSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        shipping_session = request.session.get('checkout',{}).get('shipping',[])
        if not shipping_session:
            return Response({"message": "No se encontró información de envío en la sesión."}, status=400)
        
        seleccion_envio = shipping_session[int(data.get('id'))-1]
        if not seleccion_envio:
            return Response({"message": "Opción de envío no encontrada."}, status=400)

        request.session['checkout']['envio_seleccionado'] = seleccion_envio
        request.session['checkout']['datos_envio'] = data
        request.session.modified = True

        if data['metodo_envio'] == 'pickup_point':
            target_id = int(data.get('point_id'))
            sucursales = seleccion_envio.get('sucursales', [])
            sucursal = next((s for s in sucursales if s['point_id'] == target_id), None)

        pago_total,_,_,_,_,_ = obtener_total_checkout(request)

        response = {
            "carrier_name": seleccion_envio['carrier_name'],
            "service_name": seleccion_envio['service_name'],
            "domicilio_entrega": f"{data['calle_domicilio']} {data['altura_domicilio']}" if data['metodo_envio'] == 'standard_delivery' else f"{sucursal['nombre']} - {sucursal['direccion']}",
            "costo_envio": formato_pesos(seleccion_envio['precio']),
            "fecha_entrega": fecha_humana(seleccion_envio['fecha_entrega']),
            "pago_total": formato_pesos(pago_total)
        }

        return Response({"data": response}, status=200)

class RetiroLocalAPI(APIView):
    def post(self, request: HttpRequest):
        checkout_data = request.session.get('checkout',{})
        if checkout_data.get('datos_envio'):
            del checkout_data['datos_envio']
        if checkout_data.get('shipping'):
            del checkout_data['shipping']
        checkout_data['envio_seleccionado'] = {
            "carrier_name": "Retiro en local",
            "service_name": "Retiro en local",
            "precio": 0,
            "fecha_entrega": None
        }

        precio_total,_,_,_,_,_ = obtener_total_checkout(request)

        request.session['checkout'] = checkout_data
        request.session.modified = True

        # * PATCH CODE1
        direccion = "Calle Falsa 123, Ciudad, País"
        horario_atencion = "Lunes a Viernes de 9:00 a 18:00"

        return Response({"direccion": direccion, "horario_atencion": horario_atencion,"precio_total": formato_pesos(precio_total)}, status=200)