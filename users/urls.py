from django.urls import path
from .views import (
    cerrar_sesion,
    mi_perfil,
    LoginAPIView,
    RegisterView,
    MiCuentaView,
    check_auth,
    RecuperarCuentaView,
    VerificarTokenView,
    NuevaContraseñaView,
    ver_pedido,
    VerPedidoAPIView,
    review_pedido,
    CrearReseñaView
    )

app_name = "users"

urlpatterns = [
    path('logout/',cerrar_sesion,name="logout"),
    path('micuenta/',mi_perfil,name="perfil"),
    path('api/login/', LoginAPIView.as_view(), name='api_login'),
    path('api/register/',RegisterView.as_view(),name='api_register'),
    path('api/micuenta/',MiCuentaView.as_view(),name="api_micuenta"),
    path('api/check_auth/',check_auth,name="api_check_auth"),
    path('api/recuperar-cuenta/',RecuperarCuentaView.as_view(),name="api_recuperar_cuenta"),
    path('api/verificar-token/',VerificarTokenView.as_view(),name="api_verificar_token"),
    path('api/nueva-contraseña/',NuevaContraseñaView.as_view(),name="api_nueva_contraseña"),
    path('pedido/<str:order_id>/',ver_pedido,name="ver_pedido"),
    path('api/ver-pedido/',VerPedidoAPIView.as_view(),name="api_ver_pedido"),
    path('reviews/<str:token>/',review_pedido,name="review_pedido"),
    path('api/crear-reseña/',CrearReseñaView.as_view(),name="api_crear_reseña"),
    
]
