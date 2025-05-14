from django.contrib import admin
from .forms import EspecificacionTecnicaForm
from .models import Marca, Categoria, SubCategoria, Producto, ImagenProducto, Atributo, EspecificacionTecnica, CategoriaEspecificacion,Etiquetas,ColorProducto
from django.utils.html import format_html

class AtributoInline(admin.TabularInline):
    model = Atributo
    extra = 1
    classes = ['collapse']

class ImagenProductoInline(admin.StackedInline):
    model = ImagenProducto
    extra = 0
    readonly_fields = ['miniatura']
    classes = ['collapse']

    def miniatura(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: contain;" />', obj.imagen.url)
        return "No hay imagen"

    miniatura.short_description = "Preview"

class EtiquetasInline(admin.TabularInline):
    model = Etiquetas
    extra = 1
    classes = ['collapse']

class ColoresInline(admin.TabularInline):
    model = ColorProducto
    extra = 1
    classes = ['collapse']

class EspecificacionTecnicaInline(admin.StackedInline):
    model = EspecificacionTecnica
    extra = 0
    form = EspecificacionTecnicaForm
    classes = ['collapse']

class ProductoAdmin(admin.ModelAdmin):
    inlines = [AtributoInline, ImagenProductoInline, ColoresInline,EspecificacionTecnicaInline,EtiquetasInline]
    list_display = ['nombre', 'sku', 'marca', 'sub_categoria','inhabilitar']
    search_fields = ['nombre', 'sku']
    list_filter = ['marca', 'sub_categoria']
    readonly_fields = ['precio','slug']

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False  # Oculta de la barra lateral

@admin.register(CategoriaEspecificacion)
class CategoriaEspecificacionAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False

admin.site.register(Producto, ProductoAdmin)
admin.site.register(Categoria)
admin.site.register(SubCategoria)