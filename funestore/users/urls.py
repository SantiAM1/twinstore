from django.urls import path
from .views import facturacion_view,iniciar_sesion,registarse,cerrar_sesion

app_name = "users"

urlpatterns = [
    path('facturacion/',facturacion_view,name='facturacion'),
    path('login/',iniciar_sesion,name="login"),
    path('singup/',registarse,name="singup"),
    path('logout/',cerrar_sesion,name="logout")
]
