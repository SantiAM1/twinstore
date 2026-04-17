from .models import Carrito
from django.db.models import Sum
from django.http import HttpRequest
from core.decorators import excluir_de_public

@excluir_de_public(retorno={})
def carrito_total(request:HttpRequest):
    if request.path.startswith('/admin/'):
        return {}
    total_productos = 0

    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        total_productos = carrito.pedidos.aggregate(total=Sum('cantidad'))['total'] or 0

    else:
        carrito: dict = request.session.get('carrito', {})
        total_productos = sum(val['cantidad'] for val in carrito.values())

    return {'total_productos': total_productos if total_productos > 0 else 0}
