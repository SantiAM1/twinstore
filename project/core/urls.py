from django.urls import path
from .views import home,local,cargar_productos_excel,buscar_productos

app_name = "core"

urlpatterns = [
    path('', home, name="home"),
    path('local/', local, name="local"),
    path('cargar-productos/', cargar_productos_excel, name='cargar_excel'),
    path('api/buscar-productos/',buscar_productos,name="buscar_prod")
]
