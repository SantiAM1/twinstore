from django.urls import path
from .views import home,local,cargar_productos_excel

app_name = "core"

urlpatterns = [
    path('', home, name="home"),
    path('local/', local, name="local"),
    path('cargar-productos/', cargar_productos_excel, name='cargar_excel'),
]
