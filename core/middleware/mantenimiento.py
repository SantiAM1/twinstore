from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.core.cache import cache
from core.utils import get_configuracion_tienda
from django.http import HttpRequest

class MantenimientoGlobalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        es_mantenimiento = request.path.startswith('/mantenimiento')
        es_admin = request.path.startswith('/panel-admin-twinstore')

        usuario = request.user
        es_staff = usuario.is_authenticated and (usuario.is_staff or usuario.is_superuser)

        modo_mantenimiento = cache.get('modo_mantenimiento')
        if modo_mantenimiento is None:
            try:
                config = get_configuracion_tienda()
                modo_mantenimiento = config['mantenimiento']
                cache.set('modo_mantenimiento', modo_mantenimiento, 60)
            except:
                modo_mantenimiento = False

        if modo_mantenimiento and not es_staff:
            if not es_mantenimiento and not es_admin:
                return redirect(reverse('pagina_mantenimiento'))

        if not modo_mantenimiento and es_mantenimiento:
            return redirect(reverse('core:home'))

        return self.get_response(request)
