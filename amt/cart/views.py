from django.shortcuts import redirect, get_object_or_404,render,HttpResponse
from .models import Producto, Carrito, Pedido

# Create your views here.
def ver_carrito(request):
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        return render(request, 'ver_carrito.html', {'carrito': carrito})
    else:
        pass

def agregar_al_carrito(request, producto_id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)
        cantidad = int(request.POST.get('cantidad', 1))

        if request.user.is_authenticated:
            carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
            carrito.agregar_producto(producto, cantidad)
            return redirect('products:producto', product_name=producto.nombre)
        else:
            pass

def eliminar_del_carrito(request,pedido_id):
    carrito = get_object_or_404(Carrito,usuario=request.user)
    pedido = get_object_or_404(Pedido,id=pedido_id,carrito=carrito)
    pedido.delete()
    return redirect('cart:ver_carrito')

def cart_update(request, pedido_id):
    carrito = get_object_or_404(Carrito, usuario=request.user)
    pedido = get_object_or_404(Pedido, id=pedido_id, carrito=carrito)

    action = request.POST.get('action')

    if action == "increment":
        pedido.cantidad += 1
        pedido.save()
    elif action == "decrement":
        if pedido.cantidad > 1:
            pedido.cantidad -= 1
            pedido.save()
        else:
            pedido.delete()
            return redirect('cart:ver_carrito')  # Redirigir directamente si eliminamos el pedido

    return redirect('cart:ver_carrito')