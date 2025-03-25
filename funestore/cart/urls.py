from django.urls import path
from .views import agregar_al_carrito,ver_carrito,eliminar_del_carrito,cart_update,cart_update_session,cart_delete_session,realizar_pedido

app_name = 'cart'

urlpatterns = [
    path('agregar/<int:producto_id>/', agregar_al_carrito, name='agregar'),
    path('ver/', ver_carrito, name='ver_carrito'),
    path('eliminar/<int:pedido_id>/', eliminar_del_carrito, name='eliminar'),
    path('update/<int:pedido_id>',cart_update,name="update"),
    path('update_session/<int:id>',cart_update_session,name="update_sesion"),
    path('eliminar_session/<int:id>',cart_delete_session,name="eliminar_sesion"),
    path('realizar-pedido/',realizar_pedido,name="realizar_pedido")
]
