from django.shortcuts import redirect, get_object_or_404,render,HttpResponse
from .models import Producto, Carrito, Pedido
import mercadopago
from django.conf import settings
from django.http import JsonResponse
from users.models import PerfilUsuario
from django.utils import timezone
import uuid
from datetime import timedelta
from django.utils import timezone
from datetime import timedelta


# Create your views here.
# ----- Preferencias de MP ----- #

# ! Falta agregar los datos de envio!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def preference_mp(request, numero, carrito_id, dni_cuit, ident_type, email):
    site_url = f'{settings.MY_NGROK_URL}'
    perfil = getattr(request.user, 'perfil', None)
    direccion_envio = request.user.direcciones_envio.first() if request.user.is_authenticated else None

    argentina_tz = timezone.get_fixed_timezone(-180)

    expiration_from = timezone.localtime(timezone.now(), argentina_tz).isoformat()
    expiration_to = timezone.localtime(timezone.now() + timedelta(days=1), argentina_tz).isoformat()

    preference_data = {
        "items": [
            {
                "id": f"carrito-{carrito_id}",
                "title": "Compra en Funestore",
                "description": "Productos electrónicos - Funestore.com.ar",
                "quantity": 1,
                "currency_id": "ARS",
                "unit_price": float(numero),
                "category_id": "electronics"
            }
        ],
        "payer": {
            "name": perfil.nombre if perfil and perfil.nombre else "Cliente",
            "surname": perfil.apellido if perfil and perfil.apellido else "",
            "email": email,
            "identification": {
                "type": ident_type,
                "number": dni_cuit
            },
            "address": {
                "zip_code": direccion_envio.codigo_postal if direccion_envio else "",
                "street_name": direccion_envio.calle if direccion_envio else "",
                "street_number": direccion_envio.altura if direccion_envio else ""
            }
        },
        "back_urls": {
            "success": f"https://{site_url}/payment/success",
            "failure": f"https://{site_url}/payment/failure",
            "pending": f"https://{site_url}/payment/pendings"
        },
        "auto_return": "approved",
        "notification_url": f"https://{site_url}/payment/webhook/",
        "statement_descriptor": "FUNESTORE",
        "external_reference": str(carrito_id),
        "expires": True,
        "expiration_date_from": expiration_from,
        "expiration_date_to": expiration_to,
    }
    print(preference_data)
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]

    return preference

# ----- Realizar pedido -----#
def realizar_pedido(request):
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    perfil, create = PerfilUsuario.objects.get_or_create(user = request.user)
    ident_type = "CUIT" if perfil.tipo_factura in ["A", "C"] else "DNI"
    preference = preference_mp(request,carrito.get_total(),carrito.id,perfil.dni_cuit,ident_type,request.user.email)
    public_key = f"{settings.MERCADOPAGO_PUBLIC_KEY}"
    return render(request, 'cart/realizar_pedido.html', {
        'carrito': carrito,
        'preference_id': preference.get("id", ""),
        'public_key':public_key
        })

# ----- Ver el carro -----#
def ver_carrito(request):
    #step Si esta autenticado
    if request.user.is_authenticated:
        # perfil, create = PerfilUsuario.objects.get_or_create(user = request.user)
        # if not perfil.dni_cuit:
        #     return redirect('users:facturacion')
        # carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        # ident_type = "CUIT" if perfil.tipo_factura in ["A", "C"] else "DNI"
        # preference = preference_mp(request,carrito.get_total(),carrito.id,perfil.dni_cuit,ident_type,request.user.email)
        # public_key = f"{settings.MERCADOPAGO_PUBLIC_KEY}"
        # return render(request, 'cart/ver_carrito.html', {
        # 'carrito': carrito,
        # 'preference_id': preference.get("id", ""),
        # 'public_key':public_key
        # })
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        return render(request, 'cart/ver_carrito.html', {
            'carrito': carrito,
        })


    #step Si NO! esta autenticado
    datos_facturacion = request.session.get('datos_facturacion')
    if not datos_facturacion:
        return redirect('users:facturacion')
    if 'anon_cart_id' not in request.session:
        request.session['anon_cart_id'] = f"anon-{uuid.uuid4()}"
    carrito_id = request.session['anon_cart_id']
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

    ident_type = "CUIT" if datos_facturacion['tipo_factura'] in ["A", "C"] else "DNI"
    preference = preference_mp(request,total_compra,carrito_id,datos_facturacion['dni_cuit'],ident_type,datos_facturacion['email'])
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