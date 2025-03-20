from django.urls import path
from .views import home,local

app_name = "core"

urlpatterns = [
    path('', home, name="home"),
    path('local/', local, name="local"),
]
