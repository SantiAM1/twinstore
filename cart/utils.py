from django.http import HttpRequest
import mercadopago
from django.conf import settings
from django.utils import timezone
from products.models import ColorProducto,Producto
from payment.models import EstadoPedido,Cupon,HistorialCompras,ComprobanteTransferencia
from users.models import DatosFacturacion
from cart.models import Carrito, CheckOutData,Pedido
from payment.models import TicketDePago
from django.core.cache import cache
from django.db import transaction
import random,string,uuid
import pytz
from datetime import timedelta
from django.core import signing

def crear_historial_compras(request:HttpRequest,checkout_serializer:dict,forma_pago,comprobante=None,) -> tuple[str, str|None]:
    """
    Crea un historial de compras.

    Devuelve el merchant_order_id generado para el historial de compras creado.
    """
    carrito = obtener_carrito(request)
    productos = obtener_json_productos(carrito,request)
    precio_total,_,_ = obtener_total(carrito)
    checkout = obtener_crear_checkout(request)

    precio_total -= checkout.descuento if checkout and checkout.descuento else 0
    precio_total += checkout.adicional if checkout and checkout.adicional else 0
    
    merchant_order_id = _generar_identificador_unico()
    init_point = None

    with transaction.atomic():
        historial = HistorialCompras.objects.create(
            usuario=request.user,
            productos=productos,
            total_compra=precio_total,
            estado='pendiente' if forma_pago in ['mercado_pago','mixto','transferencia'] else 'confirmado',
            forma_de_pago=forma_pago,
            merchant_order_id=merchant_order_id,
        )

        if forma_pago in ['transferencia','mixto']:
            if not comprobante:
                raise ValueError("El comprobante de transferencia es obligatorio para pagos por transferencia o mixtos.")
            generar_comprobante(historial,comprobante)

        crear_facturacion(checkout_serializer,historial)

        if forma_pago in ['mercado_pago','mixto']:
            ticket = generar_ticket(historial,checkout,forma_pago)
            data = ticket.get_preference_data()
            metadata = data.get('metadata')
            firma = {"firma":signing.dumps(metadata)}
            try:
                preference = preference_mp(data['numero'],data['ticket_id'],data['dni_cuit'],data['ident_type'],data['email'],data['nombre'],data['apellido'],data['codigo_postal'],data['calle_nombre'],data['calle_altura'],firma,backurl_success=data['backurl_success'],backurl_fail=data['backurl_fail'])
                init_point = preference.get("init_point", "")
            except ValueError as e:
                pass

        if checkout and checkout.cupon_id:
            borrar_cupon(checkout.cupon_id,historial)

        request.session.pop('checkout_id', None)
        request.session.modified = True
        checkout.delete()

    borrar_carrito(request)
    return merchant_order_id,init_point

def obtener_json_productos(carrito:list[dict],request:HttpRequest) -> list[dict]:
    """
    Obtiene la lista de productos en formato JSON desde el carrito del usuario autenticado o anónimo.

    Se utilizar para guardar el historial de compras y limpiar el carrito después de la compra.

    Ejemplo de salida:
    ```json
    {
        'producto':(Blanco) iPhone 14 Pro Max,
        'cantidad':2,
        'precio_unitario':1000,
        'subtotal':2000,
        'imagen': '/media/iphone14promax.jpg',
    }
    ```
    """
    detalle_productos = []
    for item in carrito:
        detalle_productos.append({
            'producto': item['nombre'],
            'cantidad': item['cantidad'],
            'precio_unitario': float(item['precio'] / item['cantidad']),
            'subtotal': float(item['precio']),
            'imagen': item['imagen'],
        })
    return detalle_productos

def obtener_carrito(request:HttpRequest) -> list[dict]:
    """
    Obtiene el carrito del usuario autenticado o anónimo.

    Estructura del carrito:
    ```json
    {
        'id':pedido.id,
        'producto':producto,
        'cantidad':pedido.cantidad,
        'precio':pedido.get_total_precio(),
        'nombre': pedido.get_nombre_producto(),
        'imagen': producto.get_imagen(),
        'precio_anterior':(producto.precio_anterior)*pedido.cantidad if producto.descuento > 0 else None,
        'descuento':(producto.precio_anterior - producto.precio)*pedido.cantidad if producto.descuento > 0 else 0
    }
    """
    if hasattr(request, "_cached_carrito"):
        return request._cached_carrito

    key = (
        f"carrito_user_{request.user.id}"
        if request.user.is_authenticated
        else f"carrito_anon_{request.session.session_key}"
    )

    carrito = cache.get(key)
    if carrito:
        request._cached_carrito = carrito
        return carrito
    
    carrito_unico = []
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        pedidos = carrito.pedidos.select_related('producto','color').prefetch_related('producto__colores__imagenes_color','producto__imagenes_producto')

        for pedido in pedidos:
            producto = pedido.producto
            if pedido.producto.inhabilitar:
                pedido.delete()
                continue
            carrito_unico.append({
                'id':pedido.id,
                'producto':producto,
                'cantidad':pedido.cantidad,
                'precio':pedido.get_total_precio(),
                'nombre': pedido.get_nombre_producto(),
                'imagen': producto.get_imagen_carro(color_id=pedido.color.id if pedido.color else None),
                'precio_anterior':(producto.precio_anterior)*pedido.cantidad if producto.descuento > 0 else None,
                'descuento':(producto.precio_anterior - producto.precio)*pedido.cantidad if producto.descuento > 0 else 0
            })
    else:
        if 'anon_cart_id' not in request.session:
            request.session['anon_cart_id'] = f"anon-{uuid.uuid4()}"
        carrito_session = request.session.get('carrito', {})

        ids_productos = [int(k.split('-')[0]) for k in carrito_session.keys()]
        productos = {p.id: p for p in Producto.objects.filter(id__in=ids_productos).prefetch_related('colores__imagenes_color', 'imagenes_producto')}

        ids_colores = [int(k.split('-')[1]) for k in carrito_session.keys() if k.split('-')[1] != 'null']
        colores = {c.id: c for c in ColorProducto.objects.filter(id__in=ids_colores)}

        for producto_id, cantidad in carrito_session.items():
            producto_id_str, color_id_str = producto_id.split('-')
            producto = productos.get(int(producto_id_str))
            color = colores.get(int(color_id_str)) if color_id_str != 'null' else None

            if not producto or producto.inhabilitar:
                continue

            nombre_producto = f"({color.nombre}) {producto.nombre}" if color else producto.nombre
            carrito_unico.append({
                'id': f"{producto.id}-{color_id_str}",
                'producto': producto,
                'cantidad': cantidad,
                'precio': producto.precio * cantidad,
                'nombre': nombre_producto,
                'imagen': producto.get_imagen_carro(color_id=color.id if color else None),
                'precio_anterior': (producto.precio_anterior)*cantidad if producto.descuento > 0 else None,
                'descuento': (producto.precio_anterior - producto.precio)*cantidad if producto.descuento > 0 else 0
            })

    cache.set(key, carrito_unico , timeout=60)
    request._cached_carrito = carrito_unico

    return carrito_unico if carrito_unico else None

def obtener_total(carrito):
    """
    Calcula el total, subtotal y descuento del carrito proporcionado.\n
    Retorna una tupla con (precio_total, precio_subtotal, descuento).
    """
    if not carrito:
        return 0,0,0
    precio_subtotal = sum(item['precio_anterior'] if item['precio_anterior'] else item['precio'] for item in carrito)
    precio_total = sum(item['precio'] for item in carrito)
    descuento = sum(item['descuento'] for item in carrito)
    return precio_total,precio_subtotal,descuento

def clear_carrito_cache(request:HttpRequest):
    """
    Limpia la caché del carrito del usuario autenticado o anónimo.
    """
    key = (
        f"carrito_user_{request.user.id}"
        if request.user.is_authenticated
        else f"carrito_anon_{request.session.session_key}"
    )
    cache.delete(key)

def borrar_carrito(request:HttpRequest):
    """
    Borra el carrito del usuario autenticado o anónimo.
    """
    try:
        carrito = Carrito.objects.get(usuario=request.user)
        carrito.pedidos.all().delete()
        carrito.delete()
    except Carrito.DoesNotExist:
        pass
    clear_carrito_cache(request)

def merge_carts(request, user):
    """
    Fusiona el carrito anónimo almacenado en la sesión con el carrito del usuario autenticado.\n
    Esto se utiliza cuando un usuario inicia sesión después de haber agregado productos a su carrito como usuario anónimo.
    """
    anon_cart = request.session.get('carrito', {})
    if not anon_cart:
        return

    carrito, _ = Carrito.objects.get_or_create(usuario=user)

    with transaction.atomic():
        for key, cantidad in anon_cart.items():
            producto_id_str, color_id_str = key.split('-')
            producto_id = int(producto_id_str)
            color_id = int(color_id_str) if color_id_str != 'null' else None

            try:
                producto = Producto.objects.get(id=producto_id, inhabilitar=False)
            except Producto.DoesNotExist:
                continue

            pedido = carrito.pedidos.filter(producto_id=producto_id)
            if color_id:
                pedido = pedido.filter(color_id=color_id)
            pedido = pedido.first()

            nueva_cantidad = min(cantidad + (pedido.cantidad if pedido else 0), 5)

            if pedido:
                pedido.cantidad = nueva_cantidad
                pedido.save(update_fields=['cantidad'])
            else:
                Pedido.objects.create(
                    carrito=carrito,
                    producto=producto,
                    color_id=color_id,
                    cantidad=nueva_cantidad,
                )

    if 'carrito' in request.session:
        del request.session['carrito']
    request.session.modified = True

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
        if not HistorialCompras.objects.filter(merchant_order_id=nuevo_id).exists():
            return nuevo_id

def borrar_cupon(cupon_id:int,historial:HistorialCompras) -> float:
    """
    Elimina el cupón aplicado y registra el estado en el historial de compras.
    """
    try:
        cupon = Cupon.objects.get(id=cupon_id)
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

def crear_facturacion(data:dict,historial:HistorialCompras) -> None:
    """
    Crea los datos de facturación para un historial de compras.
    """
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
        direccion=data['direccion'],
        localidad=data['localidad'],
    )

def obtener_crear_checkout(request:HttpRequest) -> CheckOutData|None:
    """
    Obtiene el checkout.

    Si no existe, crea un nuevo registro de CheckOutData y lo devuelve.
    """
    checkout_id = request.session.get('checkout_id','')
    if checkout_id:
        try:
            checkout_data = CheckOutData.objects.get(id=checkout_id, usuario=request.user)
            return checkout_data
        except CheckOutData.DoesNotExist:
            return None
    else:
        checkout_data = CheckOutData.objects.create(
            usuario=request.user,
        )
        request.session['checkout_id'] = checkout_data.id
    return checkout_data

def generar_ticket(historial:HistorialCompras,checkout:CheckOutData,forma_pago:str) -> TicketDePago:
    """
    Genera un ticket de pago para el historial de compras proporcionado.
    """
    if forma_pago not in ['mercado_pago','mixto']:
        raise ValueError("La forma de pago debe ser 'mercado_pago' o 'mixto' para generar un ticket.")

    if forma_pago == 'mercado_pago':
        monto = historial.total_compra
    else:
        monto = checkout.mixto
        if not monto:
            raise ValueError("El monto para el pago mixto no puede ser nulo o cero.")
        
    ticket = TicketDePago.objects.create(
        historial=historial,
        monto=monto,
    )
    return ticket

def generar_comprobante(historial:HistorialCompras,file) -> ComprobanteTransferencia:
    comprobante = ComprobanteTransferencia.objects.create(
        historial=historial,
        file=file,
    )
    return comprobante

def preference_mp(numero, carrito_id, dni_cuit, ident_type, email,nombre,apellido,codigo_postal,calle_nombre,calle_altura,firma,backurl_success,backurl_fail):
    """
    Genera una preferencia de pago para Mercado Pago.
    """
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
            "success": f"https://{site_url}/{backurl_success}",
            "failure": f"https://{site_url}/{backurl_fail}",
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