from core.models import EventosPromociones
from django.utils import timezone
from django.core.cache import cache
from core.utils import get_configuracion_tienda

def evento_activo_context(request):
    def obtener_evento():
        ahora = timezone.now()
        return EventosPromociones.objects.filter(
            fecha_inicio__lte=ahora,
            fecha_fin__gte=ahora,
            activo=True,
            mostrar_en_inicio=True
        ).first()

    evento_activo = cache.get_or_set('evento_activo_context', obtener_evento, 60)
    
    return {'evento_activo': evento_activo}

def config_context(request):
    today = timezone.now().date()
    return {'config': get_configuracion_tienda(), 'today': today}