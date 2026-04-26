from django.urls import path
from .views import webhook_mercadopago,payment_success,pendings,failure,InitPointMPView

app_name = "payment"

urlpatterns = [
    path("webhook/", webhook_mercadopago, name="webhook"),
    path("success/",payment_success,name="success"),
    path("failure/",failure,name="failure"),
    path("pendings/",pendings,name="pendings"),
    path("api/init-point-mp/",InitPointMPView.as_view(),name="init_point_mp"),
]