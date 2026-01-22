from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.core.cache import cache
from core.utils import get_configuracion_tienda,gen_cache_key
from django.http import HttpRequest

class MantenimientoGlobalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if request.tenant.schema_name == 'public':
            return self.get_response(request)
        es_mantenimiento = request.path.startswith('/mantenimiento')
        es_admin = request.path.startswith('/admin')

        usuario = request.user
        es_staff = usuario.is_authenticated and (usuario.is_staff or usuario.is_superuser)

        MANTENIMIENTO_CACHE_KEY = gen_cache_key('modo_mantenimiento',request)
        modo_mantenimiento = cache.get(MANTENIMIENTO_CACHE_KEY)
        if modo_mantenimiento is None:
            try:
                config = get_configuracion_tienda(request)
                modo_mantenimiento = config['mantenimiento']
                cache.set(MANTENIMIENTO_CACHE_KEY, modo_mantenimiento, 60)
            except:
                modo_mantenimiento = False

        if modo_mantenimiento and not es_staff:
            if not es_mantenimiento and not es_admin:
                return redirect(reverse('pagina_mantenimiento'))

        if not modo_mantenimiento and es_mantenimiento:
            return redirect(reverse('core:home'))

        return self.get_response(request)
