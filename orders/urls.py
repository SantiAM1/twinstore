from django.urls import path
from .views import (
    finalizar_compra,
    ValidarCuponView,
    ValidarFacturacionView,
    ValidarFormaPagoView,
    FinalizarCompraView,
    pedido_exitoso
)

app_name = 'orders'

urlpatterns = [
    path('finalizar-compra/',finalizar_compra,name="finalizar_compra"),
    path("exitoso/<int:merchant_order_id>",pedido_exitoso,name="pedido_exitoso"),
    path("api/validar-cupon/",ValidarCuponView.as_view(),name="validar-cupon"),
    path("api/validar-facturacion/",ValidarFacturacionView.as_view(),name="api_validar_facturacion"),
    path("api/validar-pago/",ValidarFormaPagoView.as_view(),name="api_validar_pago"),
    path("api/finalizar-compra/",FinalizarCompraView.as_view(),name="api_finalizar_compra"),
]
