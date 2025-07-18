from django.urls import path
from .views import webhook_mercadopago,payment_success,pendings,failure,subir_comprobante,GenerarComprobante

app_name = "payment"

urlpatterns = [
    path("webhook/", webhook_mercadopago, name="webhook"),
    path("success/",payment_success,name="success"),
    path("failure/",failure,name="failure"),
    path("pendings/",pendings,name="pendings"),
    path("comprobante/<str:id_signed>/",subir_comprobante,name="comprobante"),
    path("api/generarcomprobante/",GenerarComprobante.as_view(),name="generar-comprobante")
]