from django.shortcuts import redirect, get_object_or_404,render,HttpResponse
from .models import Producto, Carrito, Pedido

# Create your views here.
def home(request):
    if not request.user.is_authenticated:
        pass
    else:
        carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
        return render(request,'ver_carrito.html',{
            'carrito':carrito
        })

def agregar_al_carrito(request, producto_id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)
        cantidad = int(request.POST.get('cantidad', 1))

        if not request.user.is_authenticated:
            carrito_sesion = request.session.get('carrito', {})

            if str(producto_id) in carrito_sesion:
                carrito_sesion[str(producto_id)]['cantidad'] += cantidad
            else:
                carrito_sesion[str(producto_id)] = {
                    'producto_id': producto_id,
                    'cantidad': cantidad,
                }
            request.session['carrito'] = carrito_sesion
            return HttpResponse(f"Usuario: {request.session.get('carrito', {})}")

        else:
            carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
            try:
                pedido_existente = carrito.pedidos.get(producto=producto)
                pedido_existente.cantidad += cantidad
                pedido_existente.save()
            except Pedido.DoesNotExist:
                pedido = Pedido.objects.create(producto=producto, cantidad=cantidad)
                carrito.pedidos.add(pedido)

        return redirect('products:producto', product_name=producto.nombre)
