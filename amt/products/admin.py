from django.contrib import admin
from .models import Marca, Categoria, SubCategoria, Producto, ImagenProducto

# Register your models here.
admin.site.register(Marca)
admin.site.register(Categoria)
admin.site.register(SubCategoria)
admin.site.register(Producto)
admin.site.register(ImagenProducto)