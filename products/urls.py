from django.urls import path
from .views import (
    productos,
    subcategoria_view,
    slug_dispatcher,
    editar_producto_view,
    busqueda_view,
    agregar_color,
    eliminar_color,
    agregar_imagenes,
    asociar_color_img
    )

app_name = "products"

urlpatterns = [
    path('',productos,name="grid"),
    path('busqueda/',busqueda_view,name="busqueda_view"),
    path('agregar_color/<int:producto_id>/',agregar_color,name="agregar_color"),
    path('agregar_imagenes/<int:producto_id>/',agregar_imagenes,name="agregar_imagenes"),
    path('asociar_color_img/<int:producto_id>/',asociar_color_img,name="asociar_color_img"),
    path('eliminar_color/<int:color_id>/',eliminar_color,name="eliminar_color"),
    path('<slug:categoria>/<slug:subcategoria>/',subcategoria_view,name="subcategoria_view"),
    path('<slug:slug>/', slug_dispatcher, name='slug_dispatcher'),
    path('editar/<int:pk>',editar_producto_view,name="editar_producto"),
]
