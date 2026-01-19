from django.contrib import admin
from django.utils.html import format_html
from django.templatetags.static import static
from django.urls import resolve

from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from unfold.paginator import InfinitePaginator
from unfold.contrib.inlines.admin import NonrelatedTabularInline
from unfold.admin import TabularInline

from .utils import ProductoResource,IngresoStockResource
from core.utils import get_configuracion_tienda

from .models import (
        Producto,
        ImagenProducto,
        Atributo,
        EspecificacionTecnica,
        Etiquetas,
        ColorProducto,
        ReseñaProducto,
        TokenReseña,
        IngresoStock,
        Proveedor,
        LoteStock,
        MovimientoStock,
        AjusteStock,
        Categoria,
        SubCategoria,
        Marca,
    )

@admin.register(TokenReseña)
class TokenReseñaAdmin(ModelAdmin):
    pass

@admin.register(Categoria)
class CategoriaAdmin(ModelAdmin):
    search_fields = ['nombre']

@admin.register(SubCategoria)
class SubCategoriaAdmin(ModelAdmin):
    search_fields = ['nombre']

@admin.register(Marca)
class MarcaAdmin(ModelAdmin):
    search_fields = ['nombre']

@admin.register(Etiquetas)
class EtiquetasAdmin(ModelAdmin):
    pass

class IngresarStockInline(NonrelatedTabularInline):
    model = IngresoStock
    extra = 0
    fields = ('producto_color', 'costo_unitario', 'cantidad', 'proveedor')
    readonly_fields = ('creado_por',)
    tab = True
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):        
        if db_field.name == "producto_color":
            resolve_match = resolve(request.path)
            if 'object_id' in resolve_match.kwargs:
                producto_id = resolve_match.kwargs['object_id']
                kwargs["queryset"] = ColorProducto.objects.filter(producto_id=producto_id)
            else:
                kwargs["queryset"] = ColorProducto.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form_queryset(self, obj):
        """
        Gets all nonrelated objects needed for inlines. Method must be implemented.
        """
        return self.model.objects.filter(producto=obj)

    def get_formset(self, request, obj = None, **kwargs):
        self.request = request
        return super().get_formset(request, obj, **kwargs)

    def save_new_instance(self, parent, instance:IngresoStock):
        """
        Extra save method which can for example update inline instances based on current
        main model object. Method must be implemented.
        """
        instance.creado_por = self.request.user
        instance.producto = parent
        instance.save()

class EspecificacionTecnicaInline(TabularInline):
    model = EspecificacionTecnica
    extra = 1
    tab = True

class AtributoInline(TabularInline):
    model = Atributo
    extra = 1
    tab = True

class ReseñasInline(TabularInline):
    model = ReseñaProducto
    tab = True
    extra = 0

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario')
        
    raw_id_fields = ('usuario',)

class ColorProductoInline(TabularInline):
    model = ColorProducto
    tab = True
    extra = 1

class ImagenProductoInline(TabularInline):
    model = ImagenProducto
    tab = True
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "color":
            resolve_match = resolve(request.path)
            if 'object_id' in resolve_match.kwargs:
                producto_id = resolve_match.kwargs['object_id']
                kwargs["queryset"] = ColorProducto.objects.filter(producto_id=producto_id)
            else:
                kwargs["queryset"] = ColorProducto.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Producto)
class ProductoAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    resource_class = ProductoResource
    paginator = InfinitePaginator
    list_per_page = 15
    inlines = [ColorProductoInline, ImagenProductoInline,ReseñasInline,AtributoInline,EspecificacionTecnicaInline,IngresarStockInline]
    list_display = ('portada','nombre', 'sku', 'precio', 'sub_categoria', 'marca','precio_final', 'descuento', 'inhabilitar')
    list_select_related = ('sub_categoria','marca','evento',)

    search_fields = ('nombre', 'sku',)
    list_filter = ('marca','sub_categoria','evento','inhabilitar',)

    readonly_fields = ('sku','precio_final','slug','updated_at')

    fieldsets = (
        (None, {
            'fields': ('nombre', 'sku', 'descripcion_seo', 'marca','sub_categoria'),
        }),
        ('Precios y descuento', {
            'fields': ('precio_divisa', 'descuento','precio_final'),
        }),
        ('Evento promocional', {
            'fields': ('evento',),
        }),
        ('Opciones avanzadas', {
            'classes': ('collapse',),
            'fields': ('slug', 'inhabilitar','etiquetas'),
        }),
    )

    def get_inlines(self, request, obj):
        """
        Sobrescribimos este método para filtrar inlines dinámicamente.
        """
        # 1. Obtenemos la lista base de inlines (copia para no afectar otras request)
        inlines_actuales = super().get_inlines(request, obj).copy()
        
        # 2. Obtenemos la configuración
        config = get_configuracion_tienda()
        
        # 3. Aplicamos la lógica: Si NO es estricto, lo sacamos.
        if config.get('modo_stock') != 'estricto':
            if IngresarStockInline in inlines_actuales:
                inlines_actuales.remove(IngresarStockInline)
                
        return inlines_actuales

    def portada(self, obj):
        if obj.imagenes_producto.exists():
            return format_html(f"<img src='{obj.imagenes_producto.all()[0].imagen.url}' width='50' height='50' />")
        return format_html(f"<img src='{static('img/prod_default.webp')}' width='50' height='50' />")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sub_categoria').prefetch_related('imagenes_producto')

@admin.register(MovimientoStock)
class MovimientoStockAdmin(ModelAdmin):
    list_display = ('producto','producto_color','tipo', 'cantidad', 'lote', 'venta', 'fecha')
    list_per_page = 20
    paginator = InfinitePaginator
    is_popup = True

    list_select_related = ('producto', 'producto_color', 'lote', 'venta', 'venta__usuario','producto_color__producto',)

@admin.register(AjusteStock)
class AjusteStockAdmin(ModelAdmin):
    list_display = ('producto','color','venta', 'cantidad_faltante', 'creado_en')

@admin.register(IngresoStock)
class IngresoStockAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    resource_class = IngresoStockResource
    paginator = InfinitePaginator
    list_per_page = 15
    list_display = ('producto','id','producto_color','costo_unitario', 'cantidad', 'proveedor','creado_por', 'fecha_ingreso')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('id')

@admin.register(Proveedor)
class ProveedorAdmin(ModelAdmin):
    list_display = ('nombre', 'telefono','direccion', 'email','cuit')

@admin.register(LoteStock)
class LoteStockAdmin(ModelAdmin):
    list_display = ('ingreso', 'id','cantidad_disponible', 'costo_unitario', 'fecha_ingreso')
