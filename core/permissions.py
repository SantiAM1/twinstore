from rest_framework.permissions import BasePermission
from django.core.cache import cache
from .utils import get_configuracion_tienda

class BloquearSiMantenimiento(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        es_staff = user.is_authenticated and (user.is_staff or user.is_superuser)

        modo_mantenimiento = cache.get('modo_mantenimiento')
        if modo_mantenimiento is None:
            try:
                config = get_configuracion_tienda()
                modo_mantenimiento = config['mantenimiento']
                cache.set('modo_mantenimiento', modo_mantenimiento, 10)
            except:
                modo_mantenimiento = False

        if modo_mantenimiento and not es_staff:
            return False

        return True
