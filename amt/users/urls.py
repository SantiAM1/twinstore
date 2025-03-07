from django.urls import path
from .views import inicio_sesion, cerrar_sesion,registro,perfil,verificar_email

app_name = "users"

urlpatterns = [
    path('login/', inicio_sesion, name="login"),
    path('logout/', cerrar_sesion, name="logout"),
    path('registro/', registro, name="registro"),
    path('verificar/<uuid:token>/', verificar_email, name="verificar_email"),
    path('perfil/',perfil,name="perfil")
]
