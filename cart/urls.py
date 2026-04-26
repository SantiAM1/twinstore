from django.urls import path
from .views import (
    ver_carrito,
    AgregarAlCarritoView,
    EliminarPedidoView,
    ActualizarPedidoView,
)

app_name = 'cart'

urlpatterns = [
    path('', ver_carrito, name='ver_carrito'),
    path('api/agregar_al_carrito/',AgregarAlCarritoView.as_view(),name='api_agregar_carrito'),
    path('api/eliminar_pedido/',EliminarPedidoView.as_view(),name="api_eliminar_pedido"),
    path('api/actualizar_pedido/',ActualizarPedidoView.as_view(),name="api_actualizar_pedido"),
]
