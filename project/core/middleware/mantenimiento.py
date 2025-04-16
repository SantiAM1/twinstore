from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.core.cache import cache
from core.models import ModoMantenimiento  # ajustá según tu app

class MantenimientoGlobalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        es_mantenimiento = request.path.startswith('/mantenimiento')
        es_admin = request.path.startswith('/admin')

        usuario = request.user
        es_staff = usuario.is_authenticated and (usuario.is_staff or usuario.is_superuser)

        # Obtener estado en caché (más rápido que consultar DB siempre)
        modo_mantenimiento = cache.get('modo_mantenimiento')
        if modo_mantenimiento is None:
            try:
                modo_mantenimiento = ModoMantenimiento.objects.first().activo
                cache.set('modo_mantenimiento', modo_mantenimiento, 10)  # dura 10 seg
            except:
                modo_mantenimiento = False  # por defecto activo

        # Si está activo y no es staff ni admin, redirige
        if modo_mantenimiento and not es_staff:
            if not es_mantenimiento and not es_admin:
                return redirect(reverse('pagina_mantenimiento'))

        # Si no está activo y entra a /mantenimiento, lo echamos
        if not modo_mantenimiento and es_mantenimiento:
            return redirect(reverse('core:home'))

        return self.get_response(request)
