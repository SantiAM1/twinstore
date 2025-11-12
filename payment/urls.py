from django.urls import path
from .views import webhook_mercadopago,payment_success,pendings,failure,SubirComprobante,DatosComprobante,InitPointMPView,ArrepentimientoPostView

app_name = "payment"

urlpatterns = [
    path("webhook/", webhook_mercadopago, name="webhook"),
    path("success/",payment_success,name="success"),
    path("failure/",failure,name="failure"),
    path("pendings/",pendings,name="pendings"),
    path("api/subir-comprobante/",SubirComprobante.as_view(),name="subir_comprobante"),
    path("api/datos-comprobante/",DatosComprobante.as_view(),name="datos_comprobante"),
    path("api/init-point-mp/",InitPointMPView.as_view(),name="init_point_mp"),
    path("api/solicitar-arrepentimiento/",ArrepentimientoPostView.as_view(),name="solicitar_arrepentimiento"),
]