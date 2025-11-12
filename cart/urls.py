from django.urls import path
from .views import (
    ver_carrito,
    finalizar_compra,
    AgregarAlCarritoView,
    EliminarPedidoView,
    ActualizarPedidoView,
    EnviarWtapView,
    ValidarCuponView,
    ValidarPagoMixtoView,
    CheckoutView,
    ValidarFacturacionView,
    AdicionalesCheckoutView
)

app_name = 'cart'

urlpatterns = [
    path('', ver_carrito, name='ver_carrito'),
    path('finalizar-compra/',finalizar_compra,name="finalizar_compra"),
    path('api/agregar_al_carrito/',AgregarAlCarritoView.as_view(),name='api_agregar_carrito'),
    path('api/eliminar_pedido/',EliminarPedidoView.as_view(),name="api_eliminar_pedido"),
    path('api/actualizar_pedido/',ActualizarPedidoView.as_view(),name="api_actualizar_pedido"),
    path("api/enviar_wtap/", EnviarWtapView.as_view(), name="enviar_wtap"),
    path("api/validar-cupon/",ValidarCuponView.as_view(),name="validar-cupon"),
    path("api/pagomixto/",ValidarPagoMixtoView.as_view(),name="api_pagomixto"),
    path("api/checkout/finalizar/",CheckoutView.as_view(),name="api_checkout"),
    path("api/checkout/validar-facturacion/",ValidarFacturacionView.as_view(),name="api_validar_facturacion"),
    path("api/checkout/adicionales/",AdicionalesCheckoutView.as_view(),name="api_adicionales_checkout"),
]
