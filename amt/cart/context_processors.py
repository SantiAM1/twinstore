from .models import Carrito

def carrito_total(request):
    if request.user.is_authenticated:
        carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
        total_productos = sum([pedido.cantidad for pedido in carrito.pedidos.all()]) if carrito else 0
        total_precio = sum([pedido.producto.precio * pedido.cantidad for pedido in carrito.pedidos.all()]) if carrito else "0.00"
        total_precio = '0.00' if total_precio == 0 else total_precio
    else:
        total_precio = '0.00'
        total_productos = '0'
    return {'total_precio': total_precio,'total_productos':total_productos}