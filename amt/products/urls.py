from django.urls import path
from .views import categoria,subcategoria,producto_view

app_name = "products"

urlpatterns = [
    path('<str:categoria>/', categoria, name="categoria"),
    path('<str:categoria>/<str:sub_categoria>/', subcategoria, name="subcategoria"),
    path('producto/<str:product_name>',producto_view,name='producto')
]
