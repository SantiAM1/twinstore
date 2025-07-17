from django.http import Http404,HttpRequest
from products.models import ColorProducto,Producto
from payment.models import EstadoPedido,Cupon,HistorialCompras
from users.models import DatosFacturacion
from cart.models import Carrito
from django.shortcuts import get_object_or_404

def json_productos(request:HttpRequest) -> list:
    if request.user.is_authenticated:
        carrito = get_object_or_404(Carrito, usuario=request.user)
        # * Armamos el detalle de productos
        productos = []
        for pedido in carrito.pedidos.all():
            productos.append({
                'sku': pedido.producto.sku,
                'nombre': pedido.get_nombre_producto(),
                'precio_unitario': float(pedido.producto.precio),
                'cantidad': pedido.cantidad,
                'subtotal': float(pedido.get_total_precio()),
                'proveedor':pedido.producto.proveedor
            })
        # * Borramos el carrito y pedidos
        carrito.pedidos.all().delete()
        carrito.delete()
    else:
        carrito = request.session['carrito']
        if not carrito:
            raise Http404("Carrito vacio")
        productos = []
        for producto_id,cantidad in carrito.items():
            producto_id_str, color_str = producto_id.split('-') 
            if color_str != 'null':
                color = get_object_or_404(ColorProducto, id=int(color_str))
            else:
                color = None
            producto = get_object_or_404(Producto,id=int(producto_id_str))
            nombre_producto = f"({color.nombre}) {producto.nombre}" if color_str != 'null' else producto.nombre
            productos.append({
                'sku': producto.sku,
                'nombre':nombre_producto,
                'precio_unitario':float(producto.precio),
                'cantidad':cantidad,
                'subtotal':float(producto.precio)*cantidad,
                'proveedor':producto.proveedor
            })
        # * Borrar el carrito
        del request.session['carrito']
        request.session.modified = True
    return productos

def borrar_cupon(request:HttpRequest,historial:HistorialCompras) -> None:
    if request.session.get('cupon',''):
        cupon_id = request.session['cupon'].get('id')
        try:
            cupon = Cupon.objects.get(id=int(cupon_id))
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
        calle=data['calle'],
        ciudad=data['ciudad'],
        calle_detail=data['calle_detail'],
    )