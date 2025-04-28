from django.contrib import admin
from .forms import EspecificacionTecnicaForm
from .models import Marca, Categoria, SubCategoria, Producto, ImagenProducto, Atributo, EspecificacionTecnica, CategoriaEspecificacion,Etiquetas
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

    def has_add_permission(self, request, obj):
        if obj and obj.imagenes.count() >= 5:
            return False
        return super().has_add_permission(request, obj)

    def miniatura(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: contain;" />', obj.imagen.url)
        return "No hay imagen"

    miniatura.short_description = "Preview"

class EtiquetasInline(admin.TabularInline):
    model = Etiquetas
    extra = 1
    classes = ['collapse']

class EspecificacionTecnicaInline(admin.StackedInline):
    model = EspecificacionTecnica
    extra = 0
    form = EspecificacionTecnicaForm
    classes = ['collapse']

class ProductoAdmin(admin.ModelAdmin):
    inlines = [AtributoInline, ImagenProductoInline, EspecificacionTecnicaInline,EtiquetasInline]
    list_display = ['nombre', 'sku', 'marca', 'sub_categoria']
    search_fields = ['nombre', 'sku']
    list_filter = ['marca', 'sub_categoria']
    readonly_fields = ['precio','slug']

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False
    
@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False  # Oculta de la barra lateral

@admin.register(SubCategoria)
class SubcategoriaAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False

@admin.register(CategoriaEspecificacion)
class CategoriaEspecificacionAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False

admin.site.register(Producto, ProductoAdmin)
admin.site.register(Etiquetas)