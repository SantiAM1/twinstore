from .models import Carrito,CheckOutData
from django.db.models import Sum
from django.http import HttpRequest

def carrito_total(request:HttpRequest):
    total_productos = 0

    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        total_productos = carrito.pedidos.aggregate(total=Sum('cantidad'))['total'] or 0

    else:
        carrito = request.session.get('carrito', {})
        total_productos = sum(cantidad for cantidad in carrito.values())

    return {'total_productos': total_productos if total_productos > 0 else 0}

def limpiar_checkout(request:HttpRequest):
    checkout_id = request.session.get('checkout_id')
    if checkout_id:
        CheckOutData.objects.filter(id=checkout_id, completado=False).delete()
        request.session.pop('checkout_id', None)
        request.session.modified = True
    return {}

# def carrito_total(request,type=None,pedido=None,descuento=0):
#     if request.user.is_authenticated:
#         carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
#         pedidos = list(carrito.pedidos.all()) if carrito else []
#         total_productos = sum(pedido.cantidad for pedido in pedidos)
#         total_precio = sum(pedido.producto.precio * pedido.cantidad for pedido in pedidos) or 0
#         if type == 'views':
#             sub_total = pedido.get_total_precio() if pedido else 0
#         else:
#             sub_total = None
#     else:
#         carrito = request.session.get('carrito',{})
#         pedidos = []
#         for producto_id,cantidad in carrito.items():
#             producto_id_str, color_id_str = producto_id.split('-')
#             producto_id = int(producto_id_str)
#             producto = get_object_or_404(Producto,id=producto_id)
#             pedidos.append({
#                 'producto_id':f"{producto_id}-{color_id_str}",
#                 'cantidad' : cantidad,
#                 'sub_total' : producto.precio * cantidad
#             })
#         total_precio = sum(pedido['sub_total'] for pedido in pedidos) if pedidos else 0
#         total_productos = sum(pedido['cantidad'] for pedido in pedidos)
#         if type == 'views' and pedido is not None:
#             sub_total = next(
#                 (item['sub_total'] for item in pedidos if item['producto_id'] == str(pedido)),
#                 Decimal('0.00')
#             )
#         else:
#             sub_total = None

#     if type== "api" and request.session.get('cupon',''):
#         cupon = request.session['cupon']
#         cupon_descuento = cupon.get('descuento')

#         descuento = Decimal(total_precio)*Decimal(cupon_descuento)/100
#         total_precio -= descuento
#     elif request.session.get('cupon',''):
#         del request.session['cupon']
#         request.session.modified = True

#     if request.session.get('adicional_mp',{}) and type != "api":
#         del request.session['adicional_mp']
#         request.session.modified = True

#     return {'total_precio': total_precio,'total_productos':total_productos,'sub_total':sub_total,'descuento':descuento}