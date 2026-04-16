from django.urls import path
from .views import CotizarEnvioAPI,ObtenerSucursalesAPI,ValidarEnvioAPI,RetiroLocalAPI

app_name = 'shipping'

urlpatterns = [
    path('api/cotizar/', CotizarEnvioAPI.as_view(), name='cotizar_envio'),
    path('api/obtener-sucursales/', ObtenerSucursalesAPI.as_view(), name='obtener_sucursales'),
    path('api/validar-envio/', ValidarEnvioAPI.as_view(), name='validar_envio'),
    path('api/retiro-local/', RetiroLocalAPI.as_view(), name='retiro_local'),
]