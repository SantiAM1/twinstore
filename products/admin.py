from django.contrib import admin,messages
from django.utils.html import format_html
from django.templatetags.static import static
from django.urls import resolve

from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from unfold.paginator import InfinitePaginator
from unfold.contrib.inlines.admin import NonrelatedTabularInline,NonrelatedStackedInline
from unfold.admin import TabularInline,StackedInline
from unfold.decorators import action

from .utils import ProductoResource,IngresoStockResource
from core.utils import get_configuracion_tienda

from .models import (
        Producto,
        ImagenProducto,
        Atributo,
        EspecificacionTecnica,
        Etiquetas,
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
        TipoAtributo,
        ValorAtributo,
        Variante
    )

@admin.register(TipoAtributo)
class TipoAtributoAdmin(ModelAdmin):
    readonly_fields = ['slug']

@admin.register(ValorAtributo)
class ValorAtributoAdmin(ModelAdmin):
    search_fields = ['valor', 'tipo__nombre']
    readonly_fields = ['link']
    fieldsets = (
        (None,{
            'fields':('tipo','valor','metadatos','link')
        }),
    )

    def link(self, obj):
        return format_html('<a href="https://htmlcolorcodes.com/es/" target="_blank" rel="noopener noreferrer" style="color: blue">Link para acceder a los colores.</a>')

@admin.register(Variante)
class VarianteAdmin(ModelAdmin):
    readonly_fields = ['sku']
    autocomplete_fields = ['valores']

@admin.register(TokenReseña)
class TokenReseñaAdmin(ModelAdmin):
    readonly_fields = ['usuario','token','producto']

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
    search_fields = ['nombre']

@admin.register(Atributo)
class AtributoAdmin(ModelAdmin):
    search_fields = ['nombre','valor']

class IngresarStockInline(TabularInline):
    model = IngresoStock
    extra = 0
    fields = ('variante','costo_unitario', 'cantidad', 'proveedor')
    readonly_fields = ('creado_por',)
    tab = True
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):        
        if db_field.name == "variante":
            resolve_match = resolve(request.path)
            if 'object_id' in resolve_match.kwargs:
                producto_id = resolve_match.kwargs['object_id']
                kwargs["queryset"] = Variante.objects.filter(producto_id=producto_id)
            else:
                kwargs["queryset"] = Variante.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # def get_form_queryset(self, obj):
    #     """
    #     Gets all nonrelated objects needed for inlines. Method must be implemented.
    #     """
    #     return self.model.objects.filter(producto=obj)

    # def get_formset(self, request, obj = None, **kwargs):
    #     self.request = request
    #     return super().get_formset(request, obj, **kwargs)

    # def save_new_instance(self, parent, instance:IngresoStock):
    #     """
    #     Extra save method which can for example update inline instances based on current
    #     main model object. Method must be implemented.
    #     """
    #     instance.creado_por = self.request.user
    #     instance.producto = parent
    #     instance.save()

class VarianteInline(TabularInline):
    model = Variante
    extra = 0
    tab = True

    readonly_fields = ['sku']
    autocomplete_fields = ['valores']

class EspecificacionTecnicaInline(TabularInline):
    model = EspecificacionTecnica
    extra = 1
    tab = True

class ReseñasInline(TabularInline):
    model = ReseñaProducto
    tab = True
    extra = 0

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario')
        
    raw_id_fields = ('usuario',)

class ImagenProductoInline(TabularInline):
    model = ImagenProducto
    tab = True
    extra = 1
    autocomplete_fields = ['variante']

@admin.register(Producto)
class ProductoAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    resource_class = ProductoResource
    paginator = InfinitePaginator
    list_per_page = 15
    inlines = [ImagenProductoInline,ReseñasInline,EspecificacionTecnicaInline,IngresarStockInline,VarianteInline]
    list_display = ('portada','nombre', 'precio', 'sub_categoria', 'marca','precio_final', 'descuento', 'inhabilitar','evento_activo')
    list_select_related = ('sub_categoria','marca','evento',)

    search_fields = ('nombre', 'sku',)
    list_filter = ('marca','sub_categoria','evento','inhabilitar',)
    actions = ['agregar_a_evento']

    autocomplete_fields = ['etiquetas','atributos']

    readonly_fields = ('sku','precio_final','slug','updated_at',)

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
            'fields': ('slug', 'inhabilitar','etiquetas','atributos'),
        }),
    )

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        
        for instance in instances:
            if isinstance(instance, IngresoStock):
                if not instance.pk:
                    instance.creado_por = request.user
            
            instance.save()
        
        formset.save_m2m()

    @action(description="Agregar al evento activo",icon="event_available",url_path="agregar-a-evento")
    def agregar_a_evento(self, request, queryset):
        from core.models import EventosPromociones
        evento = EventosPromociones.objects.first()
        if evento and evento.esta_activo:
            modificados = 0
            for prod in queryset:
                if not prod.evento:
                    prod.evento = evento
                    prod.save()
                    modificados += 1
            
            if modificados > 0:
                self.message_user(
                    request, 
                    f"{modificados} producto/s se sumaron al evento", 
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request, 
                    "No hubo cambios.", 
                    messages.WARNING
                )
        else:
            self.message_user(
                    request, 
                    "No hay un evento activo.", 
                    messages.WARNING
                )

    def get_inlines(self, request, obj):
        inlines_actuales = super().get_inlines(request, obj).copy()
        config = get_configuracion_tienda()
        
        if config.get('modo_stock') != 'estricto':
            if IngresarStockInline in inlines_actuales:
                inlines_actuales.remove(IngresarStockInline)
                
        return inlines_actuales

    def evento_activo(self,obj):
        if obj.evento:
            return obj.evento.nombre_evento
        return "-"

    def portada(self, obj):
        if obj.imagenes_producto.exists():
            return format_html(f"<img src='{obj.imagenes_producto.all()[0].imagen.url}' width='50' height='50' />")
        return format_html(f"<img src='{static('img/prod_default.webp')}' width='50' height='50' />")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'sub_categoria', 
            'marca', 
            'evento'
        ).prefetch_related(
            'imagenes_producto',
            'variantes',
        )

@admin.register(MovimientoStock)
class MovimientoStockAdmin(ModelAdmin):
    list_display = ('producto','tipo', 'cantidad', 'lote', 'venta', 'fecha')
    list_per_page = 20
    paginator = InfinitePaginator
    is_popup = True

    list_select_related = ('producto', 'lote', 'venta', 'venta__usuario',)

@admin.register(AjusteStock)
class AjusteStockAdmin(ModelAdmin):
    list_display = ('producto','variante','venta', 'cantidad_faltante', 'creado_en')

@admin.register(IngresoStock)
class IngresoStockAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    resource_class = IngresoStockResource
    paginator = InfinitePaginator
    list_per_page = 15
    list_display = ('producto','id','costo_unitario', 'cantidad', 'proveedor','creado_por', 'fecha_ingreso')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('id')

@admin.register(Proveedor)
class ProveedorAdmin(ModelAdmin):
    list_display = ('nombre', 'telefono','direccion', 'email','cuit')

@admin.register(LoteStock)
class LoteStockAdmin(ModelAdmin):
    list_display = ('ingreso', 'id','cantidad_disponible', 'costo_unitario', 'fecha_ingreso')
