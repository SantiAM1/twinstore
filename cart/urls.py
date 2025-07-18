from django.urls import path
from .views import (
    ver_carrito,
    realizar_pedido,
    CalcularPedidoView,
    AgregarAlCarritoView,
    EliminarPedidoView,
    ActualizarPedidoView,
    generar_presupuesto,
    EnviarWtapView,
    ValidarCuponView,
    ValidarPagoMixtoView,
    InitPointMPView
)

app_name = 'cart'

urlpatterns = [
    path('ver/', ver_carrito, name='ver_carrito'),
    path('realizar-pedido/',realizar_pedido,name="realizar_pedido"),
    path('api/calcular-pedido/', CalcularPedidoView.as_view(), name='api_calcular_pedido'),
    path('api/agregar_al_carrito/',AgregarAlCarritoView.as_view(),name='api_agregar_carrito'),
    path('api/eliminar_pedido/',EliminarPedidoView.as_view(),name="api_eliminar_pedido"),
    path('api/actualizar_pedido/',ActualizarPedidoView.as_view(),name="api_actualizar_pedido"),
    path('presupuestar/',generar_presupuesto,name="presupuestar"),
    path("api/enviar_wtap/", EnviarWtapView.as_view(), name="enviar_wtap"),
    path("api/validar-cupon/",ValidarCuponView.as_view(),name="validar-cupon"),
    path("api/pagomixto/",ValidarPagoMixtoView.as_view(),name="api_pagomixto"),
    path("api/initpointmp/",InitPointMPView.as_view(),name="api_initpointmp")
]
