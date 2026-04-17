from django.http import JsonResponse
from django.core.cache import cache
from .utils import get_configuracion_tienda
from functools import wraps

def bloquear_si_mantenimiento(view_func):
    """
    Decorador para bloquear el acceso a vistas si el modo de mantenimiento está activo.
    Si el usuario es staff o superuser, se le permite el acceso.
    """
    def _wrapped_view(request, *args, **kwargs):
        usuario = request.user
        es_staff = usuario.is_authenticated and (usuario.is_staff or usuario.is_superuser)

        modo_mantenimiento = cache.get('modo_mantenimiento')
        if modo_mantenimiento is None:
            try:
                config = get_configuracion_tienda(request)
                modo_mantenimiento = config['mantenimiento']
                cache.set('modo_mantenimiento', modo_mantenimiento, 10)
            except:
                modo_mantenimiento = False

        if modo_mantenimiento and not es_staff:
            return JsonResponse({'error': 'Mantenimiento en curso'}, status=503)

        return view_func(request, *args, **kwargs)
    return _wrapped_view

def excluir_de_public(request=None,retorno={}):
    """
    Decorador para excluir vistas del esquema público.
    Si el usuario está en el esquema público, se devuelve un JSON vacío o el retorno especificado.
    """
    if request:
        return (hasattr(request, 'tenant') and request.tenant.schema_name == 'public')
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if hasattr(arg, 'tenant'):
                    request = arg
                    break
            if not request and 'request' in kwargs:
                request = kwargs['request']
            if request and hasattr(request, 'tenant') and request.tenant.schema_name == 'public':
                return retorno
            return func(*args, **kwargs)
        return wrapper
    return decorator