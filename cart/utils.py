from django.http import HttpRequest
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404

from products.models import Producto,Variante
from users.models import User
from core.utils import get_configuracion_tienda,gen_cache_key

from .types import CarritoDict
from .models import Carrito,Pedido

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

def obtener_total(carrito:list[CarritoDict]):
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