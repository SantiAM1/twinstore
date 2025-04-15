from django.contrib import admin
from .forms import EspecificacionTecnicaForm

from .models import Marca, Categoria, SubCategoria, Producto, ImagenProducto, Atributo, EspecificacionTecnica, CategoriaEspecificacion

# ----- Inline para especificaciones técnicas -----
class EspecificacionTecnicaInline(admin.StackedInline):
    model = EspecificacionTecnica
    extra = 1
    form = EspecificacionTecnicaForm

# ----- Admin de Producto -----
class ProductoAdmin(admin.ModelAdmin):
    inlines = [EspecificacionTecnicaInline]
    list_display = ('nombre', 'marca', 'sub_categoria', 'precio')

# ----- Registro de modelos -----
admin.site.register(Marca)
admin.site.register(Categoria)
admin.site.register(SubCategoria)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(ImagenProducto)
admin.site.register(Atributo)
admin.site.register(CategoriaEspecificacion)