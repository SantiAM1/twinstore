from django.http import HttpRequest
from django.db import transaction
from django.core import signing
from django.contrib import messages
from django.conf import settings

from products.models import Producto,Variante
from payment.models import TicketDePago,Cupon

import random,string

from cart.types import CarritoDict
from cart.utils import obtener_carrito, obtener_total, borrar_carrito
from payment.utils import preference_mp
from core.utils import get_configuracion_tienda
from decimal import Decimal

from .types import CheckoutData,Facturacion
from orders.models import Venta,EstadoPedido,DatosFacturacion,VentaDetalle

def obtener_total_checkout(request:HttpRequest):
    """
    Retorna los valores que integran el checkout.
    * precio_total: El total final a pagar.
    * adicional: El monto adicional aplicado por la forma de pago (si existe).
    * costo_envio: El costo de envío aplicado (si existe).
    * cupon: El monto descontado por el cupón aplicado (si existe).
    * monto_mercadopago: El monto que se pagará a través de Mercado Pago (si la forma de pago es mercado_pago o mixto).
    * monto_transferencia: El monto que se pagará a través de transferencia (si la forma de pago es mixto).
    """
    precio_total, adicional, costo_envio, cupon, monto_mercadopago, monto_transferencia = (0,0,0,0,0,0)
    carrito = obtener_carrito(request)
    checkout_data:CheckoutData = request.session.get('checkout',{})

    # > 1. Subtotal del carrito
    precio_total,_,_ = obtener_total(carrito)

    # > 2. Aplicar descuento por cupon (si existe)
    if checkout_data.get('cupon',''):
        cupon_aplicado = precio_total*(Decimal('1') - (Decimal(checkout_data['cupon']['descuento'])/Decimal('100')))
        cupon = precio_total - cupon_aplicado
        precio_total = cupon_aplicado

    # > 3. Aplicar costo de envío (si existe)
    costo_envio = checkout_data['envio_seleccionado']['precio'] if checkout_data.get('envio_seleccionado') else 0
    precio_total += Decimal(costo_envio)
    
    # > 4. Aplicar adicional por forma de pago (si existe)
    if checkout_data.get('pago'):
        # * Mixto
        if checkout_data['pago']['es_mixto']:
            print("Calculando adicional para pago mixto...")  # Debug
            monto_transferencia = Decimal(checkout_data['pago']['monto_transferencia'])
            monto_mercadopago = round((precio_total-monto_transferencia)*Decimal(settings.MERCADOPAGO_COMMISSION),2)
            adicional = monto_mercadopago - (precio_total - monto_transferencia)
        # * Mercado Pago
        elif checkout_data['pago']['forma_de_pago'] == 'mercado_pago':
            monto_mercadopago = round(precio_total*Decimal(settings.MERCADOPAGO_COMMISSION),2)
            adicional = monto_mercadopago - precio_total

    precio_total += Decimal(adicional)
    
    return precio_total, adicional, costo_envio, cupon, monto_mercadopago, monto_transferencia


def finalizar_checkout(request: HttpRequest) -> dict[str, str]:
    """
    Obtiene desde el request todos los datos necesarios para finalizar la venta, como el carrito, el checkout, la forma de pago, etc.\n
    Genera el merchant_order_id y el init_point (si corresponde) para la venta a crear.

    Acciones JS:
    * redirect: Redirige al usuario a una URL (si fallo la validación o la sesión expiró).
    * message: Muestra un mensaje de error (usualmente para datos incompletos en el checkout).
    * init_point: Retorna el init_point generado para redirigir al usuario a Mercado Pago (si corresponde).
    * merchant_order_id: Retorna el merchant_order_id si la venta fue creada correctamente.
    """
    precio_total, _, _, _, monto_mercadopago, monto_transferencia = obtener_total_checkout(request)
    merchant_order_id = _generar_identificador_unico()
    init_point = None

    checkout:CheckoutData = request.session.get('checkout', None)
    if not checkout:
        messages.error(request, "Tu sesión ha expirado o el carrito está vacío.")
        return {"redirect": "/carro/"}
    
    required_fields = ['pago', 'envio_seleccionado', 'facturacion']
    if not all(checkout.get(field) for field in required_fields):
        return {"message": "Información de checkout incompleta. Por favor, completa todos los pasos del checkout.","type":"error"}
    
    forma_de_pago = checkout['pago']['forma_de_pago']

    with transaction.atomic():
        # * Validamos la venta
        if not validar_compra(request):
            return {"redirect": "/carro/"}
        
        # * Creamos la venta
        venta = Venta.objects.create(
            usuario=request.user,
            total_compra=precio_total,
            estado='pendiente',
            forma_de_pago=forma_de_pago,
            merchant_order_id=merchant_order_id,
        )

        # * Creamos los detalles de la venta
        carrito = obtener_carrito(request)
        crear_detalle_venta(venta, carrito)

        # * Creamos los datos de facturación
        crear_facturacion(venta, checkout['facturacion'])

        # * Generamos el ticket de pago y la preferencia de Mercado Pago (si corresponde)
        if forma_de_pago in ['mixto','mercado_pago','transferencia']:
            init_point = generar_tickets(forma_de_pago,venta,precio_total,monto_mercadopago,monto_transferencia)

        if checkout.get('cupon',None):
            borrar_cupon(request,checkout['cupon']['codigo'],venta)

        del request.session['checkout']
        request.session.modified = True
    
    borrar_carrito(request)
    return {"merchant_order_id": merchant_order_id, "init_point": init_point}

def generar_tickets(forma_de_pago:str,venta:Venta,precio_total:Decimal,monto_mercadopago:Decimal,monto_transferencia:Decimal=None) -> str|None:
    if forma_de_pago == 'mixto':
        ticket_mp = TicketDePago.objects.create(
            venta=venta,
            monto=monto_mercadopago,
        )
        TicketDePago.objects.create(
            venta=venta,
            monto=monto_transferencia,
            tipo=TicketDePago.Tipo.TRANS
        )
    elif forma_de_pago == 'mercado_pago':
        ticket_mp = TicketDePago.objects.create(
            venta=venta,
            monto=precio_total,
        )
    elif forma_de_pago == 'transferencia':
        TicketDePago.objects.create(
            venta=venta,
            monto=precio_total,
            tipo=TicketDePago.Tipo.TRANS
        )
        return None
    print("Generando preferencia de Mercado Pago...")
    data = ticket_mp.get_preference_data()
    metadata = data.get('metadata')
    firma = {"firma":signing.dumps(metadata)}
    try:
        print("Obteniendo init_point de Mercado Pago...")
        preference = preference_mp(data['numero'],data['ticket_id'],data['dni_cuit'],data['ident_type'],data['email'],data['nombre'],data['apellido'],data['codigo_postal'],data['calle_nombre'],data['calle_altura'],firma,backurl_success=data['backurl_success'],backurl_fail=data['backurl_fail'])
        init_point = preference.get("init_point", "")
    except ValueError as e:
        print(f"Error al generar la preferencia de Mercado Pago: {e}")
        init_point = None
    return init_point

def crear_detalle_venta(venta: Venta, carrito: list[CarritoDict]) -> None:
    """
    Crea los detalles de la venta masivamente (Bulk Create).
    """
    detalles_para_crear = []

    skus_variantes = [item['sku'] for item in carrito if item['variante']]
    skus_productos = [item['sku'] for item in carrito if not item['variante']]

    objs_variantes = {
        v.sku: v for v in Variante.objects.filter(sku__in=skus_variantes).select_related('producto')
    }
    
    objs_productos = {
        p.sku: p for p in Producto.objects.filter(sku__in=skus_productos)
    }

    for item in carrito:
        sku = item['sku']
        producto,variante = (None,None)

        if item['variante']:
            variante = objs_variantes.get(sku)
            if not variante:
                continue
            producto = variante.producto
        else:
            producto = objs_productos.get(sku)
            if not producto:
                continue
            variante = None

        detalle = VentaDetalle(
            venta=venta,
            producto=producto,
            variante=variante,
            cantidad=item['cantidad'],
            imagen_url=item['imagen'],
            precio_unitario=producto.precio_final,
            subtotal=item['precio'],
        )
        detalles_para_crear.append(detalle)

    if detalles_para_crear:
        VentaDetalle.objects.bulk_create(detalles_para_crear)
    
def _generar_identificador_pago():
    """
    Genera un identificador de pago.

    Ejemplo de salida: '48392017465'
    """
    return ''.join(random.choices(string.digits, k=11))

def _generar_identificador_unico():
    """
    Verifica que el identificador de pago sea único.
    """
    while True:
        nuevo_id = _generar_identificador_pago()
        if not Venta.objects.filter(merchant_order_id=nuevo_id).exists():
            return nuevo_id

def borrar_cupon(request: HttpRequest,codigo:str,venta:Venta) -> float:
    """
    Elimina el cupón aplicado y registra el estado en la Venta.
    """
    config = get_configuracion_tienda(request)
    try:
        cupon = Cupon.objects.get(codigo=codigo)
        if config['borrar_cupon']:
            cupon.delete()
        EstadoPedido.objects.create(
                venta=venta,
                estado="Cupón Aplicado (Servidor)",
                comentario=f"Cupón CÓDIGO #{cupon.codigo} del %{cupon.descuento} Aplicado en la compra"
            )
    except Cupon.DoesNotExist:
        EstadoPedido.objects.create(
            venta=venta,
            estado="Cupón Duplicado! (Servidor)",
            comentario=f"El cupón ingresado no fue encontrado. \nAccion requerida: RECHAZAR la venta y contactar con el cliente."
        )

def crear_facturacion(venta:Venta, data:Facturacion) -> None:
    """
    Crea los datos de facturación para una Venta.
    """
    DatosFacturacion.objects.create(
        venta=venta,
        nombre=data['nombre'],
        apellido=data['apellido'],
        razon_social=data['razon_social'],
        dni_cuit=data['dni_cuit'],
        condicion_iva=data['condicion_iva'],
        codigo_postal=data['codigo_postal'],
        provincia=data['provincia'],
        direccion=data['direccion'],
        localidad=data['localidad'],
    )

def validar_compra(request:HttpRequest) -> bool:
    """
    Antes de finalizar la compra, valida los siguentes campos:
    * El producto existe.
    * El producto no está inhabilitado.
    * El stock es suficiente (si el modo de stock es 'estricto').
    """
    carrito = obtener_carrito(request)
    config = get_configuracion_tienda(request)
    flag = True
    for item in carrito:
        sku = item['sku']
        producto,variante = (None,None)
        try:
            if len(sku) == 12:
                producto = Producto.objects.get(sku=sku)
            elif len(sku) == 17:
                variante = Variante.objects.get(sku=sku)
                producto = variante.producto
        except (Producto.DoesNotExist,Variante.DoesNotExist):
            messages.error(request,f"No se encontro un producto con SKU: {sku}")
            flag = False
            continue

        if producto.inhabilitar:
            messages.error(request, f"El producto {producto.nombre} está inhabilitado para la venta.")
            flag = False
            continue

        if config['modo_stock'] == 'estricto': 
            obj = variante if variante else producto
            stock_disponible = obj.obtener_stock()

            cantidad_solicitada = int(item['cantidad'])
            if stock_disponible < cantidad_solicitada:
                messages.error(request, f"Stock insuficiente para el producto {producto.nombre}.")
                messages.error(request, f"Stock disponible: {stock_disponible if stock_disponible > 0 else 'Sin stock'}. Cantidad solicitada: {cantidad_solicitada}.")
                messages.info(request, "Por favor, ajusta la cantidad en tu carrito antes de finalizar la compra.")
                flag = False

    return flag