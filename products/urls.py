from django.urls import path
from .views import (
    productos,
    subcategoria_view,
    slug_dispatcher,
    busqueda_view,
    )

app_name = "products"

urlpatterns = [
    path('',productos,name="grid"),
    path('busqueda/',busqueda_view,name="busqueda_view"),
    path('<slug:categoria>/<slug:subcategoria>/',subcategoria_view,name="subcategoria_view"),
    path('<slug:slug>/', slug_dispatcher, name='slug_dispatcher'),
]
