from django.shortcuts import get_object_or_404
from products.models import Producto
from .models import Carrito
import secrets

def carrito_total(request):
    if request.user.is_authenticated:
        carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
        pedidos = list(carrito.pedidos.all()) if carrito else []
        total_productos = sum(pedido.cantidad for pedido in pedidos)
        total_precio = sum(pedido.producto.precio * pedido.cantidad for pedido in pedidos) or "0.00"
    else:
        carrito = request.session.get('carrito',{})
        pedidos = []
        for producto_id,cantidad in carrito.items():
            producto = get_object_or_404(Producto,id=int(producto_id))
            pedidos.append({
                'producto' : producto,
                'cantidad' : cantidad,
                'total_precio' : producto.precio * cantidad
            })
        total_precio = sum(pedido['total_precio'] for pedido in pedidos) if pedidos else "0.00"
        total_productos = sum(pedido['cantidad'] for pedido in pedidos)

    if request.session.get('adicional_mp',{}):
        del request.session['adicional_mp']
        request.session.modified = True

    return {'total_precio': total_precio,'total_productos':total_productos,'nonce': secrets.token_urlsafe(16)}