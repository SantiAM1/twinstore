from django.urls import path
from .views import notification,payment_success,pendings,failure

app_name = "payment"

urlpatterns = [
    path("webhook/", notification, name="webhook"),
    path("success/",payment_success,name="success"),
    path("failure/",failure,name="failure"),
    path("pendings/",pendings,name="pendings")
]