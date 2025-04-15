from django.contrib import admin
from .forms import EspecificacionTecnicaForm
from .models import Marca, Categoria, SubCategoria, Producto, ImagenProducto, Atributo, EspecificacionTecnica, CategoriaEspecificacion
from django.utils.html import format_html

class AtributoInline(admin.TabularInline):
    model = Atributo
    extra = 1  # cantidad de filas nuevas vacías

class ImagenProductoInline(admin.StackedInline):
    model = ImagenProducto
    extra = 0
    readonly_fields = ['miniatura']

    def has_add_permission(self, request, obj):
        if obj and obj.imagenes.count() >= 5:
            return False
        return super().has_add_permission(request, obj)

    def miniatura(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: contain;" />', obj.imagen.url)
        return "No hay imagen"

    miniatura.short_description = "Preview"

# 👉 Inline para Especificaciones Técnicas
class EspecificacionTecnicaInline(admin.StackedInline):
    model = EspecificacionTecnica
    extra = 1
    form = EspecificacionTecnicaForm

# 👉 Admin principal de Producto
class ProductoAdmin(admin.ModelAdmin):
    inlines = [AtributoInline, ImagenProductoInline, EspecificacionTecnicaInline]
    list_display = ['nombre', 'sku', 'precio', 'marca', 'sub_categoria']
    search_fields = ['nombre', 'sku']
    list_filter = ['marca', 'sub_categoria']

# ----- Registro de modelos -----
admin.site.register(Marca)
admin.site.register(Categoria)
admin.site.register(SubCategoria)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Atributo)
admin.site.register(CategoriaEspecificacion)