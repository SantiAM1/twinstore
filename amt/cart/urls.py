from django.urls import path
from .views import home,agregar_al_carrito

app_name = 'cart'

urlpatterns = [
    path('', home, name="home"),
    path('agregar/<int:producto_id>/',agregar_al_carrito,name="agregar")
]
