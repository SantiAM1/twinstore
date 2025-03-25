from django.urls import path
from .views import home

app_name = "shipping"

urlpatterns = [
    path('home/',home,name="home"),
]
