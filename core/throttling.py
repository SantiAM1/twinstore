from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class CarritoThrottle(UserRateThrottle):
    scope = 'carrito'

class CalcularPedidoThrottle(UserRateThrottle):
    scope = 'calcular_pedido'

class ToggleNotificacionesThrottle(UserRateThrottle):
    scope = 'toggle_notificaciones'

class EnviarWtapThrottle(UserRateThrottle):
    scope = 'enviar_wtap'

class FiltrosDinamicosThrottle(AnonRateThrottle):
    scope = 'filtros_dinamicos'

class PrediccionBusquedaThrottle(AnonRateThrottle):
    scope = 'prediccion_busqueda'

class SolicitarComprobante(AnonRateThrottle):
    scope = 'solicitar_comprobante'