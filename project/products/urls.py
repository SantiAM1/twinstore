from django.urls import path
from .views import categoria,producto_view,buscar_productos,categoria_ajax,editar_producto_view,agregar_imagenes,eliminar_imagen

app_name = "products"

urlpatterns = [
    path('api/categoria/<str:categoria>/', categoria_ajax, name='categoria_ajax'),
    path('busqueda/',buscar_productos,name="search"),
    path('<str:categoria>/', categoria, name="categoria"),
    path('producto/<str:product_name>',producto_view,name='producto'),
    path('editar_producto/<int:pk>',editar_producto_view,name='editar_producto'),
    path('agregar_imagenes/<int:producto_id>',agregar_imagenes,name='agregar_imagenes'),
    path('eliminar_imagen/<int:img_id>',eliminar_imagen,name='eliminar_imagen'),
]
