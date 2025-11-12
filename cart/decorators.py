from django.shortcuts import redirect
from cart.utils import obtener_carrito

def requiere_carrito(view_func):
    """
    Decorador para verificar que el usuario tenga carrito no nulo
    """
    def wrapper(request, *args, **kwargs):
        carrito = obtener_carrito(request)
        if not carrito:
            return redirect('products:grid')
        return view_func(request, *args, **kwargs)
    return wrapper
        