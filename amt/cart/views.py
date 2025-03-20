from django.shortcuts import redirect, get_object_or_404,render,HttpResponse
from .models import Producto, Carrito, Pedido
import mercadopago
from django.conf import settings
from django.http import JsonResponse
from users.models import PerfilUsuario

# Create your views here.
# ----- Preferencias de MP ----- #
def preference_mp(numero):
    #* Integración con Mercado Pago
    site_url = 'ed59-181-228-88-24.ngrok-free.app'

    preference_data = {
            "items": [
                {
                    "title": "Compra en Funestore",
                    "quantity": 1,
                    "currency_id": "ARS",
                    "unit_price": float(numero)
                }
            ],
            "payer": {
                "email": "test_user_25279540@testuser.com"
            },
            "back_urls": {
            "success": f"https://{site_url}/payment/success",
            "failure": f"https://{site_url}/payment/failure",
            "pending": f"https://{site_url}/payment/pendings"
            },
            "auto_return": "approved",
            "notification_url": f"https://{site_url}/payment/webhook/"
        }
    
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]
    
    return preference

# ----- Ver el carro -----#
def ver_carrito(request):
    #step Si esta autenticado
    if request.user.is_authenticated:
        perfil, create = PerfilUsuario.objects.get_or_create(user = request.user)
        if not perfil.dni_cuit:
            return redirect('users:facturacion')
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        preference = preference_mp(carrito.get_total())
        return render(request, 'cart/ver_carrito.html', {
        'carrito': carrito,
        'preference_id': preference.get("id", ""),
        })

    #step Si NO! esta autenticado
    datos_facturacion = request.session.get('datos_facturacion')
    if not datos_facturacion:
        return redirect('users:facturacion')

    carrito = request.session.get('carrito',{})
    pedidos = []
    for producto_id,cantidad in carrito.items():
        producto = get_object_or_404(Producto,id=int(producto_id))
        imagen_url = producto.imagenes.first().imagen.url if producto.imagenes.first() else 'img/prod_default.jpg'
        pedidos.append({
            'id':producto.id,
            'producto':producto,
            'cantidad':cantidad,
            'total_precio':producto.precio*cantidad,
            'imagen_url': imagen_url,
            })
    total_compra = sum(pedido['total_precio'] for pedido in pedidos)

    preference = preference_mp(total_compra)
    return render(request,'cart/ver_carrito_cookie.html',{
        'pedidos':pedidos,
        'preference_id': preference.get("id", ""),
        })

# ----- Agregar un producto al carro -----# 
def agregar_al_carrito(request, producto_id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)
        cantidad = int(request.POST.get('cantidad', 1))

        #step Si esta autenticado
        if request.user.is_authenticated:
            carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
            #* Creacion de 'Pedido'
            carrito.agregar_producto(producto, cantidad)
            return redirect('products:producto', product_name=producto.nombre)
        
        #step Si no esta autenticado (Cookies)
        carrito = request.session.get('carrito',{})
        carrito[str(producto_id)] = carrito.get(str(producto_id),0) + cantidad
        request.session['carrito'] = carrito
        return redirect('products:producto', product_name=producto.nombre)

# ----- Eliminar un pedido -----#
def eliminar_del_carrito(request,pedido_id):
    carrito = get_object_or_404(Carrito,usuario=request.user)
    pedido = get_object_or_404(Pedido,id=pedido_id,carrito=carrito)
    pedido.delete()
    return redirect('cart:ver_carrito')

# ----- Actualizar el carro -----#

# ! Limitar el numero hasta 10 o 5
def cart_update(request, pedido_id):
    carrito = get_object_or_404(Carrito, usuario=request.user)
    pedido = get_object_or_404(Pedido, id=pedido_id, carrito=carrito)

    action = request.POST.get('action')

    #* Si se cambian las cantidad se actualiza
    if action == "increment":
        pedido.cantidad += 1
        pedido.save()
    elif action == "decrement":
        if pedido.cantidad > 1:
            pedido.cantidad -= 1
            pedido.save()
        else:
            pedido.delete()
            return redirect('cart:ver_carrito')

    return redirect('cart:ver_carrito')

# ----- Metodos Cookies -----#

#* Actualizar el carrito

# ! Limitar el numero hasta 10 o 5
def cart_update_session(request,id):
    carrito = request.session.get('carrito',{})
    action = request.POST.get('action')

    if str(id) in carrito:
        if action == "increment":
            carrito[str(id)] += 1
        elif action == "decrement":
            if carrito[str(id)] > 1:
                carrito[str(id)] -= 1
            else:
                carrito.pop(str(id)) 
    request.session['carrito'] = carrito
    return redirect('cart:ver_carrito')

#* Borrar pedido del carrito
def cart_delete_session(request,id):
    carrito = request.session.get('carrito',{})
    if str(id) in carrito:
        carrito.pop(str(id))
        request.session['carrito'] = carrito
    return redirect('cart:ver_carrito')