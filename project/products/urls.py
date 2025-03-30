from django.urls import path
from .views import categoria,producto_view,buscar_productos,categoria_ajax

app_name = "products"

urlpatterns = [
    path('api/categoria/<str:categoria>/', categoria_ajax, name='categoria_ajax'),
    path('busqueda/',buscar_productos,name="search"),
    path('<str:categoria>/', categoria, name="categoria"),
    path('producto/<str:product_name>',producto_view,name='producto'),
]
