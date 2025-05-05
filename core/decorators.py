from django.http import JsonResponse
from django.core.cache import cache
from core.models import ModoMantenimiento  # Ajustá la ruta a tu modelo

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
                modo_mantenimiento = ModoMantenimiento.objects.first().activo
                cache.set('modo_mantenimiento', modo_mantenimiento, 10)
            except:
                modo_mantenimiento = False

        if modo_mantenimiento and not es_staff:
            return JsonResponse({'error': 'Mantenimiento en curso'}, status=503)

        return view_func(request, *args, **kwargs)
    return _wrapped_view
