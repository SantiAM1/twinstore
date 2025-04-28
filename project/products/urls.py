from django.urls import path
from .views import (
    buscar_productos,
    categoria_ajax,
    editar_producto_view,
    agregar_imagenes,
    eliminar_imagen,
    categoria_subcategoria,
    subcategoria_ajax,
    slug_dispatcher,
    buscar_productos_ajax,
    gaming,
    gaming_ajax
    )

app_name = "products"

urlpatterns = [
    path('api/gaming/',gaming_ajax,name="gaming_api"),
    path('api/categoria/<slug:categoria>/', categoria_ajax, name='categoria_ajax'),
    path('api/categoria/<slug:categoria>/<slug:subcategoria>/', subcategoria_ajax, name='subcategoria_ajax'),
    path('api/buscar_productos_ajax/', buscar_productos_ajax, name='buscar_productos_ajax'),
    path('<slug:categoria>/<slug:subcategoria>/', categoria_subcategoria, name="categoria_subcategoria"),
    path('gaming/',gaming,name="gaming"),
    path('busqueda/',buscar_productos,name="search"),
    path('<slug:slug>/', slug_dispatcher, name='slug_dispatcher'),
    path('editar_producto/<int:pk>',editar_producto_view,name='editar_producto'),
    path('agregar_imagenes/<int:producto_id>',agregar_imagenes,name='agregar_imagenes'),
    path('eliminar_imagen/<int:img_id>',eliminar_imagen,name='eliminar_imagen'),
]
