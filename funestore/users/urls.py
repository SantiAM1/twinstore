from django.urls import path
from .views import facturacion_view,iniciar_sesion,registarse,cerrar_sesion,ver_pedidos,mi_perfil

app_name = "users"

urlpatterns = [
    path('facturacion/',facturacion_view,name='facturacion'),
    path('login/',iniciar_sesion,name="login"),
    path('singup/',registarse,name="singup"),
    path('logout/',cerrar_sesion,name="logout"),
    path('pedidos/',ver_pedidos,name="pedidos"),
    path('miperfil/',mi_perfil,name="perfil")
]
