from core.models import EventosPromociones
from django.utils import timezone
from django.core.cache import cache
from core.utils import get_configuracion_tienda,gen_cache_key

def evento_activo_context(request):
    if request.tenant.schema_name == 'public':
        return {}
    def obtener_evento():
        ahora = timezone.now()
        evento = EventosPromociones.objects.filter(
            fecha_inicio__lte=ahora,
            fecha_fin__gte=ahora,
            activo=True,
            mostrar_en_inicio=True
        ).first()

        return {
            "fecha_fin":evento.fecha_fin,
            "nombre_evento":evento.nombre_evento,
            "slug":evento.slug,
            "logo": evento.logo
        }

    evento_activo = cache.get_or_set(gen_cache_key('evento_activo_context'), obtener_evento, 60)
    
    return {'evento_activo': evento_activo}

def config_context(request):
    if request.tenant.schema_name == 'public':
        return {}
    today = timezone.now().date()
    return {'config': get_configuracion_tienda(request), 'today': today}