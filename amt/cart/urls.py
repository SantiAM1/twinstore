from django.urls import path
from .views import agregar_al_carrito,ver_carrito,eliminar_del_carrito,cart_update

app_name = 'cart'

urlpatterns = [
    path('agregar/<int:producto_id>/', agregar_al_carrito, name='agregar'),
    path('ver/', ver_carrito, name='ver_carrito'),
    path('eliminar/<int:pedido_id>/', eliminar_del_carrito, name='eliminar'),
    path('update/<int:pedido_id>',cart_update,name="update")
]
