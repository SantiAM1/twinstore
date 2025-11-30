from django.http import HttpRequest
import mercadopago
from django.conf import settings
from django.utils import timezone
from products.models import ColorProducto,Producto
from payment.models import EstadoPedido,Cupon,Venta,ComprobanteTransferencia,VentaDetalle
from users.models import DatosFacturacion
from cart.models import Carrito, CheckOutData,Pedido
from payment.models import TicketDePago
from django.core.cache import cache
from django.db import transaction
import random,string,uuid
import pytz
from datetime import timedelta
from django.core import signing
from django.contrib import messages
from django.shortcuts import get_object_or_404
from core.types import ConfigDict
from cart.types import CarritoDict

def crear_venta(carrito:dict,request:HttpRequest,checkout_serializer:dict,forma_pago,comprobante=None,) -> tuple[str, str|None]:
    """
    Crea una Venta.

    Devuelve el merchant_order_id generado para la Venta creada.
    """
    precio_total,_,_ = obtener_total(carrito)
    checkout = obtener_crear_checkout(request)

    precio_total -= checkout.descuento if checkout and checkout.descuento else 0
    precio_total += checkout.adicional if checkout and checkout.adicional else 0
    
    merchant_order_id = _generar_identificador_unico()
    init_point = None

    with transaction.atomic():
        venta = Venta.objects.create(
            usuario=request.user,
            total_compra=precio_total,
            estado='pendiente',
            forma_de_pago=forma_pago,
            merchant_order_id=merchant_order_id,
        )

        crear_detalle_venta(venta, carrito)

        if forma_pago in ['transferencia','mixto']:
            if not comprobante:
                raise ValueError("El comprobante de transferencia es obligatorio para pagos por transferencia o mixtos.")
            generar_comprobante(venta,comprobante)

        crear_facturacion(checkout_serializer,venta)

        if forma_pago in ['mercado_pago','mixto']:
            ticket = generar_ticket(venta,checkout,forma_pago)
            data = ticket.get_preference_data()
            metadata = data.get('metadata')
            firma = {"firma":signing.dumps(metadata)}
            try:
                preference = preference_mp(data['numero'],data['ticket_id'],data['dni_cuit'],data['ident_type'],data['email'],data['nombre'],data['apellido'],data['codigo_postal'],data['calle_nombre'],data['calle_altura'],firma,backurl_success=data['backurl_success'],backurl_fail=data['backurl_fail'])
                init_point = preference.get("init_point", "")
            except ValueError as e:
                pass

        if checkout and checkout.cupon_id:
            borrar_cupon(checkout.cupon_id,venta)

        request.session.pop('checkout_id', None)
        request.session.modified = True
        checkout.delete()

    borrar_carrito(request)
    return merchant_order_id,init_point

def crear_detalle_venta(venta:Venta,carrito:list[CarritoDict]) -> None:
    """
    Crea los detalles de la venta a partir del carrito proporcionado.
    """
    for item in carrito:
        try:
            producto = Producto.objects.get(id=item['producto_id'])
        except Producto.DoesNotExist:
            continue

        try:
            color = ColorProducto.objects.get(id=item['color_id'], producto=producto)
        except ColorProducto.DoesNotExist:
            color = None

        VentaDetalle.objects.create(
            venta=venta,
            producto=producto,
            color=color,
            cantidad=item['cantidad'],
            imagen_url = item['imagen'],
            precio_unitario=producto.precio_final,
            subtotal=item['precio'],
        )

def obtener_carrito(request:HttpRequest) -> list[CarritoDict]:
    """
    Obtiene el carrito del usuario autenticado o anónimo.

    Estructura del carrito:
    ```json
    {
        'id':pedido.id,
        'producto_id':producto.id,
        'producto':producto,
        'color_id': color.id if color else None,
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
                'producto_id':producto.id,
                'producto':producto,
                'color_id': pedido.color.id if pedido.color else None,
                'cantidad':pedido.cantidad,
                'precio':pedido.get_total_precio(),
                'nombre': pedido.get_nombre_producto(),
                'imagen': producto.get_imagen_carro(color_id=pedido.color.id if pedido.color else None),
                'precio_anterior':(producto.precio_base)*pedido.cantidad if producto.descuento > 0 else None,
                'descuento':(producto.precio_base - producto.precio_final)*pedido.cantidad if producto.descuento > 0 else 0
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
                'producto_id': producto.id,
                'producto': producto,
                'color_id': color.id if color else None,
                'cantidad': cantidad,
                'precio': producto.precio_final * cantidad,
                'nombre': nombre_producto,
                'imagen': producto.get_imagen_carro(color_id=color.id if color else None),
                'precio_anterior': (producto.precio_base)*cantidad if producto.descuento > 0 else None,
                'descuento': (producto.precio_base - producto.precio_final)*cantidad if producto.descuento > 0 else 0
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
    clear_cache_header(request)

def clear_cache_header(request:HttpRequest):
    from django.core.cache.utils import make_template_fragment_key
    key = make_template_fragment_key("header_main",[request.user.id])
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
        if not Venta.objects.filter(merchant_order_id=nuevo_id).exists():
            return nuevo_id

def borrar_cupon(cupon_id:int,venta:Venta) -> float:
    """
    Elimina el cupón aplicado y registra el estado en la Venta.
    """
    try:
        cupon = Cupon.objects.get(id=cupon_id)
        EstadoPedido.objects.create(
            venta=venta,
            estado="Cupón Aplicado (Servidor)",
            comentario=f"Cupón CÓDIGO #{cupon.codigo} del %{cupon.descuento} Aplicado en la compra"
        )
        cupon.delete()
    except Cupon.DoesNotExist:
        EstadoPedido.objects.create(
            venta=venta,
            estado="Cupón Duplicado! (Servidor)",
            comentario=f"El cupón ingresado no fue encontrado. \nAccion requerida: RECHAZAR la venta y contactar con el cliente."
        )

def crear_facturacion(data:dict,venta:Venta) -> None:
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

def generar_ticket(venta:Venta,checkout:CheckOutData,forma_pago:str) -> TicketDePago:
    """
    Genera un ticket de pago para la Venta proporcionada.
    """
    if forma_pago not in ['mercado_pago','mixto']:
        raise ValueError("La forma de pago debe ser 'mercado_pago' o 'mixto' para generar un ticket.")

    if forma_pago == 'mercado_pago':
        monto = venta.total_compra
    else:
        monto = checkout.mixto
        if not monto:
            raise ValueError("El monto para el pago mixto no puede ser nulo o cero.")
        
    ticket = TicketDePago.objects.create(
        venta=venta,
        monto=monto,
    )
    return ticket

def generar_comprobante(venta:Venta,file) -> ComprobanteTransferencia:
    comprobante = ComprobanteTransferencia.objects.create(
        venta=venta,
        file=file,
    )
    return comprobante

def validar_compra(carrito:list[CarritoDict],request:HttpRequest,config:ConfigDict) -> bool:
    """
    Antes de finalizar la compra, valida los siguentes campos:
    * El producto existe.
    * El producto no está inhabilitado.
    * El stock es suficiente (si el modo de stock es 'estricto').
    """
    flag = True
    for item in carrito:
        try:
            id = int(item['producto_id'])
            producto = Producto.objects.get(id=id)
        except Producto.DoesNotExist:
            messages.error(request, f"Producto no encontrado.")
            flag = False
            continue

        if producto.inhabilitar:
            messages.error(request, f"El producto {producto.nombre} está inhabilitado para la venta.")
            flag = False
            continue
    
        
        if config['modo_stock'] == 'estricto':
            color = None
            if item['color_id']:
                try:
                    color_id = int(item['color_id'])
                    color = ColorProducto.objects.get(id=color_id, producto=producto)
                except ColorProducto.DoesNotExist:
                    messages.error(request, f"El color seleccionado para el producto {producto.nombre} no existe.")
                    flag = False
                    continue
            
            stock_disponible = producto.obtener_stock(color)
            cantidad_solicitada = int(item['cantidad'])
            if stock_disponible < cantidad_solicitada:
                messages.error(request, f"Stock insuficiente para el producto {producto.nombre}.")
                messages.error(request, f"Stock disponible: {stock_disponible if stock_disponible > 0 else 'Sin stock'}. Cantidad solicitada: {cantidad_solicitada}.")
                messages.info(request, "Por favor, ajusta la cantidad en tu carrito antes de finalizar la compra.")
                flag = False

    return flag

def sumar_carrito(request:HttpRequest,producto:Producto,stock: int,color:ColorProducto|None = None) -> None:
    """
    Agrega un producto al carrito del usuario autenticado o anónimo.
    * Verifica el stock del producto (y color si aplica).
    """
    if 1 > stock:
        return None
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        carrito.agregar_producto(producto,stock,color)
    else:
        carrito = request.session.get('carrito', {})
        key = f"{producto.id}-{color.id if color else 'null'}"
        carrito[key] = carrito.get(key, 0) + 1
        if carrito[key] > stock:
            carrito[key] = stock
        request.session['carrito'] = carrito

def eliminar_del_carrito(request:HttpRequest,pedido_id: str | int) -> None:
    """
    Elimina un pedido del carrito del usuario autenticado o anónimo.
    """
    if request.user.is_authenticated:
        carrito = get_object_or_404(Carrito,usuario=request.user)
        pedido = get_object_or_404(Pedido,id=int(pedido_id),carrito=carrito)
        pedido.delete()
    else:
        carrito = request.session.get('carrito',{})
        carrito.pop(str(pedido_id), None)
        request.session['carrito'] = carrito

def actualizar_carrito(request:HttpRequest,pedido_id: str | int,action: str,stock_flag: bool,maximo_compra: int) -> dict:
    """
    Actualiza el carrito del usuario autenticado o anónimo.
    """
    if request.user.is_authenticated:
        pedido = Pedido.objects.filter(
            id=pedido_id, carrito__usuario=request.user
        ).select_related("producto").first()
        if not pedido:
            return {'status':404,"error":"Pedido no encontrado en el carrito."}
        
        producto = pedido.producto
        stock = producto.obtener_stock(pedido.color) if stock_flag else maximo_compra
        if action == "mas" and pedido.cantidad < stock:
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
        try:
            producto_id_str, color_id_str = key.split('-')
            producto_id = int(producto_id_str)
            color_id = int(color_id_str) if color_id_str != 'null' else None
            producto = Producto.objects.get(id=producto_id)
            if color_id:
                color = ColorProducto.objects.get(id=color_id)
            else:
                color = None
        except (Producto.DoesNotExist, ColorProducto.DoesNotExist, ValueError):
            return {'status':404,"error":"Producto o color no encontrado."}
        
        stock = producto.obtener_stock(color) if stock_flag else maximo_compra
        if key in carrito:
            if action == "mas" and carrito[key] < stock:
                carrito[key] += 1
            elif action == "menos":
                if carrito[key] > 1:
                    carrito[key] -= 1
                else:
                    carrito.pop(key)

        request.session["carrito"] = carrito
        request.session.modified = True
        cantidad = carrito.get(key, 0)
    
    return cantidad

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