from django.urls import path
from .views import datos_facturacion,iniciar_sesion,registarse

app_name = "users"

urlpatterns = [
    path('facturacion/',datos_facturacion,name='facturacion'),
    path('login/',iniciar_sesion,name="login"),
    path('singup/',registarse,name="singup")
]
