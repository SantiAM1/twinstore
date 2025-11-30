from core.models import EventosPromociones
from django.utils import timezone
from django.core.cache import cache

def evento_activo_context(request):
    evento_cache = cache.get('evento_activo_context')
    if evento_cache:
        return {'evento_activo': evento_cache}
    
    ahora = timezone.now()
    evento_activo = EventosPromociones.objects.filter(
        fecha_inicio__lte=ahora,
        fecha_fin__gte=ahora,
        activo=True,
        mostrar_en_inicio=True
    ).first()

    cache.set('evento_activo_context', evento_activo, 60)

    return {'evento_activo': evento_activo}
