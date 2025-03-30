from django.shortcuts import redirect
from cart.models import Carrito


def requiere_carrito(view_func):
    """
    Decorador para verificar que el usuario (autenticado o anónimo) tenga carrito activo.
    Si no lo tiene, lo redirige a 'core:home'.
    """
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
            if not carrito.pedidos.exists():
                return redirect('core:home')
        else:
            carrito = request.session.get('carrito', {})
            if not carrito:
                return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return wrapper
        