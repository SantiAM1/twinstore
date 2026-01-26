from django.http import HttpRequest
import mercadopago
from django.utils import timezone
from products.models import Producto,Variante
from payment.models import EstadoPedido,Cupon,Venta,ComprobanteTransferencia,VentaDetalle
from users.models import DatosFacturacion,User
from cart.models import Carrito, CheckOutData,Pedido
from payment.models import TicketDePago
from django.core.cache import cache
from django.db import transaction
import random,string
import pytz
from datetime import timedelta
from django.core import signing
from django.contrib import messages
from django.shortcuts import get_object_or_404
from core.types import ConfigDict
from cart.types import CarritoDict
from core.utils import get_configuracion_tienda,gen_cache_key
from products.utils_debug import debug_queries

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
            borrar_cupon(request,checkout.cupon_id,venta)

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
            if item['variante']:
                variante = Variante.objects.filter(sku=item['sku']).select_related('producto').first()
                producto = variante.producto
            else:
                producto = Producto.objects.get(sku=item['sku'])
                variante = None
        except (Producto.DoesNotExist,Variante.DoesNotExist):
            continue

        VentaDetalle.objects.create(
            venta=venta,
            producto=producto,
            variante=variante,
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
        "id": 1450,
        "sku": "CAS-ROJ-XL",
        "producto_id": 402,
        "nombre": "Casco Rebatible Hawk", 
        "variante": "Rojo / XL",
        "imagen": "/media/productos/casco-rojo.jpg",
        "url_producto": "/productos/motos/casco-rebatible-hawk/",
        "cantidad": 2,
        "precio": 50000,
        "tiene_descuento": true,
        "precio_anterior": 60000,
        "ahorro": 20000
    }
    """
    if hasattr(request, "_cached_carrito"):
        return request._cached_carrito

    key = (
        f"carrito_user_{request.user.id}"
        if request.user.is_authenticated
        else f"carrito_anon_{request.session.session_key}"
    )

    CART_CACHE_KEY = gen_cache_key(key,request)
    carrito = cache.get(CART_CACHE_KEY)

    if carrito:
        request._cached_carrito = carrito
        return carrito
    
    if request.user.is_authenticated:
        carrito_unico = _get_user_carrito(request)
    else:
        carrito_unico = _get_anon_carrito(request)

    cache.set(CART_CACHE_KEY, carrito_unico , timeout=60)
    request._cached_carrito = carrito_unico

    return carrito_unico if carrito_unico else None

def _get_user_carrito(request: HttpRequest) -> list[CarritoDict]:
    carrito_final: list[CarritoDict] = []
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

    pedidos = carrito.pedidos.select_related('producto','variante').prefetch_related(
        'producto__imagenes_producto',
        'variante__valores__tipo',
        'variante__valores__imagenes_asociadas',
        'variante__producto__imagenes_producto'
        )
    for pedido in pedidos:
        pedido: Pedido
        producto: Producto = pedido.producto
        if pedido.producto.inhabilitar:
            pedido.delete()
            continue
        obj = pedido.variante if pedido.variante else producto
        carrito_final.append({
            'id':pedido.id,
            'sku': obj.sku,
            'producto_id':producto.id,
            'nombre': producto.nombre,
            'variante':pedido.variante_resumen,
            'imagen': obj.get_imagen_carro(),
            'url_producto': producto.get_absolute_url(),
            'cantidad':pedido.cantidad,
            'precio':producto.precio_final*pedido.cantidad,
            'tiene_descuento':producto.precio_base != producto.precio_final,
            'precio_anterior': 0 if producto.precio_base == producto.precio_final else producto.precio_base*pedido.cantidad,
            'ahorro':(producto.precio_base - producto.precio_final)*pedido.cantidad if producto.precio_base != producto.precio_final else 0
        })
    
    return carrito_final

def _map_skus(carrito_session:dict, prefetch:bool = False):
    skus_variantes = []
    skus_productos = []

    for item_data in carrito_session.values():
        if item_data['type'] == 'var':
            skus_variantes.append(item_data['sku'])
        else:
            skus_productos.append(item_data['sku'])

    if prefetch:
        variantes_qs = list(
            Variante.objects.filter(sku__in=skus_variantes)
            .select_related('producto')
            .prefetch_related(
                'valores__tipo',
                'producto__imagenes_producto'
                )
            )
        productos_qs: list[Producto] = list(
            Producto.objects
            .filter(sku__in=skus_productos)
            .prefetch_related('imagenes_producto')
        )

    else:
        variantes_qs = list(
            Variante.objects.filter(sku__in=skus_variantes)
            .select_related('producto')
            )
        productos_qs: list[Producto] = list(
            Producto.objects
            .filter(sku__in=skus_productos)
            )

    map_variantes = {v.sku: v for v in variantes_qs}
    map_productos = {p.sku: p for p in productos_qs}

    return map_productos,map_variantes

def _get_anon_carrito(request: HttpRequest) -> list[CarritoDict]:
    """
    Crea el carrito del usuario no autenticado
    """
    carrito_session: dict = request.session.get('carrito', {})
    carrito_final: list[CarritoDict] = []

    map_productos, map_variantes = _map_skus(carrito_session,prefetch=True)

    for id, data in carrito_session.items():
        sku = data['sku']
        cantidad = data['cantidad']
        variante,producto = (None,None)

        if data['type'] == 'var':
            variante = map_variantes.get(sku)
            if variante:
                producto = variante.producto
        else:
            producto = map_productos.get(sku)
        
        if not producto:
            continue
        
        obj = variante if variante else producto

        carrito_final.append({
            'id': id,
            'sku':sku,
            'producto_id': producto.id,
            'nombre':producto.nombre,
            'variante':variante.resumen() if variante else "",
            'imagen': obj.get_imagen_carro(),
            'url_producto': producto.get_absolute_url(),
            'cantidad': cantidad,
            'precio': producto.precio_final * cantidad,
            'tiene_descuento':producto.precio_base != producto.precio_final,
            'precio_anterior': 0 if producto.precio_base == producto.precio_final else producto.precio_base*cantidad,
            'ahorro':(producto.precio_base - producto.precio_final)*cantidad if producto.precio_base != producto.precio_final else 0
        })

    return carrito_final

def merge_carts(request: HttpRequest, user: User) -> None:
    """
    Fusiona el carrito anónimo al iniciar sesión
    """
    carrito_session: dict = request.session.get('carrito', {})
    if not carrito_session:
        return

    config = get_configuracion_tienda(request)
    modo_estricto = config['modo_stock'] == 'estricto'
    maximo_global = config['maximo_compra']

    with transaction.atomic():
        carrito, _ = Carrito.objects.get_or_create(usuario=user)
        
        map_productos, map_variantes = _map_skus(carrito_session)

        existing_pedidos_map = {
            (p.producto_id, p.variante_id): p 
            for p in carrito.pedidos.all()
        }

        to_create = []
        to_update = []

        for data in carrito_session.values():
            sku = data['sku']
            cantidad_session = data['cantidad']
            
            variante, producto = (None, None)
            if data['type'] == 'var':
                variante = map_variantes.get(sku)
                producto = variante.producto if variante else None
            else:
                producto = map_productos.get(sku)

            if not producto: 
                continue

            obj = variante if variante else producto
            stock_real = obj.obtener_stock() if modo_estricto else 999999
            limit_stock = stock_real if modo_estricto else maximo_global

            key = (producto.id, variante.id if variante else None)
            pedido_existente = existing_pedidos_map.get(key)

            if pedido_existente:
                nueva_cantidad = min(cantidad_session + pedido_existente.cantidad, limit_stock)
                
                if pedido_existente.cantidad != nueva_cantidad:
                    pedido_existente.cantidad = nueva_cantidad
                    to_update.append(pedido_existente)
            else:
                nueva_cantidad = min(cantidad_session, limit_stock)
                if nueva_cantidad > 0:
                    to_create.append(Pedido(
                        carrito=carrito,
                        producto=producto,
                        variante=variante,
                        cantidad=nueva_cantidad
                    ))

        if to_create:
            Pedido.objects.bulk_create(to_create)
        
        if to_update:
            Pedido.objects.bulk_update(to_update, ['cantidad'])

    if 'carrito' in request.session:
        del request.session['carrito']
    request.session.modified = True

def obtener_total(carrito):
    """
    Calcula el total, subtotal y descuento del carrito proporcionado.\n
    Retorna una tupla con (precio_total, precio_subtotal, descuento).
    """
    if not carrito:
        return 0,0,0
    precio_subtotal = sum(item['precio_anterior'] if item['precio_anterior'] else item['precio'] for item in carrito)
    precio_total = sum(item['precio'] for item in carrito)
    descuento = sum(item['ahorro'] for item in carrito)
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

    CART_CACHE_KEY = gen_cache_key(key,request)

    cache.delete(CART_CACHE_KEY)
    clear_cache_header(request)

def clear_cache_header(request:HttpRequest):
    from django.core.cache.utils import make_template_fragment_key
    key = make_template_fragment_key("header_main",[request.tenant.schema_name,request.user.id])
    cache.delete(key)

def borrar_carrito(request:HttpRequest):
    """
    Borra el carrito del usuario autenticado.
    """
    try:
        carrito = Carrito.objects.get(usuario=request.user)
        carrito.pedidos.all().delete()
        carrito.delete()
    except Carrito.DoesNotExist:
        pass
    clear_carrito_cache(request)

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

def borrar_cupon(request: HttpRequest,cupon_id:int,venta:Venta) -> float:
    """
    Elimina el cupón aplicado y registra el estado en la Venta.
    """
    config = get_configuracion_tienda(request)
    try:
        cupon = Cupon.objects.get(id=cupon_id)
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

def sumar_carrito(request:HttpRequest,producto:Producto,stock_maximo: int,variante: Variante = None) -> None:
    """
    Agrega un producto al carrito del usuario autenticado o anónimo.
    """
    from time import time
    target_sku = variante.sku if variante else producto.sku
    if 1 > stock_maximo:
        return None
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        carrito.agregar_producto(producto,stock_maximo,variante)
        return 
    else:
        carrito: dict = request.session.get('carrito', {})
        item_id = None
        for fake_id, item_data in carrito.items():
            if item_data['sku'] == target_sku:
                item_id = fake_id
                break

        if item_id:
            nueva_cantidad = carrito[item_id]['cantidad'] + 1
            if nueva_cantidad > stock_maximo:
                nueva_cantidad = stock_maximo
            carrito[item_id]['cantidad'] = nueva_cantidad
        else:
            nuevo_id = str(int(time() * 100))
            
            carrito[nuevo_id] = {
                'sku': target_sku,
                'cantidad': 1,
                'type': "var" if variante else 'prod'
            }
        
        request.session['carrito'] = carrito
        request.session.modified = True

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

def actualizar_carrito(request:HttpRequest,pedido_id: str | int,action: str,stock_flag: bool,maximo_compra: int) -> int:
    """
    Actualiza el carrito del usuario autenticado o anónimo.
    """
    if request.user.is_authenticated:
        pedido = Pedido.objects.filter(
            id=pedido_id, carrito__usuario=request.user
        ).select_related("producto","variante").first()
        if not pedido:
            return {'status':404,"error":"Pedido no encontrado en el carrito."}
        
        producto = pedido.producto
        variante = pedido.variante
        obj = variante if variante else producto
        stock = obj.obtener_stock() if stock_flag else maximo_compra
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
        carrito: dict = request.session.get("carrito", {})
        key = str(pedido_id)
        item = carrito[key]
        if item['type'] == 'var':
            obj = Variante.objects.get(sku=item['sku'])
        else:
            obj = Producto.objects.get(sku=item['sku'])
        
        stock = obj.obtener_stock() if stock_flag else maximo_compra
        if key in carrito:
            if action == "mas" and carrito[key]['cantidad'] < stock:
                carrito[key]['cantidad'] += 1
            elif action == "menos":
                if carrito[key]['cantidad'] > 1:
                    carrito[key]['cantidad'] -= 1
                else:
                    carrito.pop(key)

        request.session["carrito"] = carrito
        request.session.modified = True
        cantidad = carrito[key]['cantidad']
    
    return cantidad

def preference_mp(numero, carrito_id, dni_cuit, ident_type, email,nombre,apellido,codigo_postal,calle_nombre,calle_altura,firma,backurl_success,backurl_fail):
    """
    Genera una preferencia de pago para Mercado Pago.
    """
    from core.utils import get_mp_config, build_absolute_uri
    site_url = f'{build_absolute_uri()}'

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

    mp_config = get_mp_config()
    sdk = mercadopago.SDK(mp_config['access'])

    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response.get("response", {})
        init_point = preference.get("init_point")

        if not init_point or not init_point.startswith("https://www.mercadopago.com"):
            raise ValueError("Init point inválido o no generado")
        
        return preference

    except Exception as e:
        raise ValueError(f"Error al generar preferencia de pago: {str(e)}")