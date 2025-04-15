from django.conf import settings
from django.shortcuts import redirect

class MantenimientoGlobalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        esta_en_mantenimiento = getattr(settings, 'PAGINA_EN_MANTENIMIENTO', False)
        es_admin = request.path.startswith('/admin')
        es_mantenimiento = request.path.startswith('/mantenimiento')

        usuario = request.user

        # Permitir navegación a staff o superusuarios incluso durante el mantenimiento
        es_staff = usuario.is_authenticated and (usuario.is_staff or usuario.is_superuser)

        # Si el sitio está en mantenimiento y el usuario no es staff
        if esta_en_mantenimiento and not es_staff:
            if not es_mantenimiento and not es_admin:
                return redirect('pagina_mantenimiento')

        # Si el sitio NO está en mantenimiento y alguien entra manualmente a /mantenimiento/
        if not esta_en_mantenimiento and es_mantenimiento:
            return redirect('inicio')

        return self.get_response(request)
