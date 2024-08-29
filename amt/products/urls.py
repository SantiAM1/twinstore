from django.urls import path
from .views import por_categoria,por_subcategoria,test

app_name = "products"

urlpatterns = [
    path('categoria/<str:categoria_nombre>/', por_categoria, name='categoria_filter'),
    path('categoria/<str:categoria_nombre>/<str:subcategoria_nombre>/', por_subcategoria, name='subcategoria_filter'),
    path('test/',test,name='test')
]