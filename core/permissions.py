from rest_framework.permissions import BasePermission
from django.core.cache import cache
from core.models import ModoMantenimiento

class BloquearSiMantenimiento(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        es_staff = user.is_authenticated and (user.is_staff or user.is_superuser)

        modo_mantenimiento = cache.get('modo_mantenimiento')
        if modo_mantenimiento is None:
            try:
                modo_mantenimiento = ModoMantenimiento.objects.first().activo
                cache.set('modo_mantenimiento', modo_mantenimiento, 10)
            except:
                modo_mantenimiento = False

        if modo_mantenimiento and not es_staff:
            print(f"🔒 Bloqueado por mantenimiento: {request.path} - {user}")
            return False

        return True
