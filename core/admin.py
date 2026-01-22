from django.contrib import admin
from unfold.admin import ModelAdmin,TabularInline, StackedInline
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.templatetags.static import static
from customers.models import Client
from unfold.sections import TableSection

from .models import (
    Tienda,
    EventosPromociones,
    HomeSection,
    HomeBanner,
    HomeBannerMedio,
    HomeCarouselBento,
    HomeProductGrid,
    MercadoPagoConfig,
    DatosBancarios,
    HomeStaticBento
)

@admin.register(MercadoPagoConfig)
class MercadoPagoConfigAdmin(ModelAdmin):
    list_display = ('public_key', 'access_token')
    readonly_fields = ['advertencia']
    
    def get_fieldsets(self, request, obj = None):
        if request.tenant.plan == Client.Plan.BASIC:
            return ((None, {'fields': ('advertencia',)}),)
        return (
                (None, {
                    'fields': ('public_key','access_token','webhook_key')
                }),
            )

    def advertencia(self, obj):
        return f"No tienes permiso para completar estos campos. Tu plan es 'Básico'"

    def has_change_permission(self, request, obj = ...):
        if request.tenant.plan == Client.Plan.BASIC:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj = ...):
        return True

@admin.register(DatosBancarios)
class DatosBancariosAdmin(ModelAdmin):
    list_display = ('banco', 'numero_cuenta', 'alias','titular_cuenta')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

class HomeCarouselBentoInline(StackedInline):
    model = HomeCarouselBento
    extra = 0

    autocomplete_fields = ['producto', 'categoria', 'subcategoria', 'marca']

    fieldsets = (
        (None, {
            'fields': (
                ('imagen', 'tamano'),
                ('slide', 'orden')
            )
        }),
        ("Seleccioná una opción", {
            'classes': ('collapse',),
            'fields': (
                ('producto', 
                'categoria', 
                'subcategoria', 
                'marca'),
            ),
        }),
    )

class HomeStaticBentoInline(StackedInline):
    model = HomeStaticBento
    extra = 0
    max_num = 8

    autocomplete_fields = ['producto', 'categoria', 'subcategoria', 'marca']

    fieldsets = (
        (None, {
            'fields': (
                ('imagen', 'color_fondo','orden'),
            )
        }),
        ("Seleccioná una opción", {
            'classes': ('collapse',),
            'fields': (
                'producto', 
                'categoria', 
                'subcategoria', 
                'marca'
            ),
        }),
    )

class HomeBannerMedioInline(TabularInline):
    model = HomeBannerMedio
    extra = 1
    max_num = 3

    fieldsets = (
        (None, {
            'fields': ('tipo','svg','titulo','descripcion','orden')
        }),
    )

class HomeProductGridInline(TabularInline):
    model = HomeProductGrid
    extra = 1
    max_num = 1

class HomeBannerInline(TabularInline):
    model = HomeBanner
    extra = 1
    max_num = 5

class SectionDetail(TableSection):
    verbose_name = "Contenido de sección"
    height = 300

    CONFIG = {
        "banner_principal": {
            "related": "banners",
            "fields": ['portada', 'orden', 'url'],
        },
        "grilla": {
            "related": "grids_productos",
            "fields": ['portada', 'criterio'],
        },
        "banner_medio": {
            "related": "banners_medios",
            "fields": ['portada','tipo','titulo'],
        },
        "static_bento": {
            "related": "static_bento",
            "fields": ['portada','color_fondo','orden']
        },
        "bento": {
            "related": "categorias",
            "fields": ['portada','tamano','slide','orden']
        }
    }

    def __init__(self, request, instance):
        config = self.CONFIG.get(instance.tipo, {})
        self.related_name = config.get("related")
        self.fields = config.get("fields",[])
        super().__init__(request, instance)

    def portada(self, instance):
        if hasattr(instance,'admin_portada'):
            return instance.admin_portada
        return "-"

@admin.register(HomeSection)
class HomeSectionAdmin(ModelAdmin):
    list_display = ['tipo','orden', 'activo']
    readonly_fields = ['preview_banner_principal','preview_banner_pequeño','preview_bento','preview_bento_estatico','preview_grilla_de_productos','como_continuar']
    list_sections = [
        SectionDetail
    ]

    fieldsets = (
        (None, {
            'fields': ('orden', 'tipo','preview_banner_principal','preview_banner_pequeño','preview_bento','preview_bento_estatico','preview_grilla_de_productos','como_continuar', 'titulo', 'subtitulo','activo')
        }),
    )

    conditional_fields = {
        'titulo': "['grilla', 'bento', 'static_bento'].includes(tipo)",
        'subtitulo': "['grilla', 'bento', 'static_bento'].includes(tipo)",
        'preview_banner_principal': "tipo == 'banner_principal'",
        'preview_banner_pequeño': "tipo == 'banner_medio'",
        'preview_bento': "tipo == 'bento'",
        'preview_bento_estatico': "tipo == 'static_bento'",
        'preview_grilla_de_productos': "tipo == 'grilla'",
        'como_continuar': "tipo != 'empty'"
    }

    def como_continuar(self,obj):
        return f'Hace click en "Guardar y continuar editando" para crear tu plantilla'

    def preview_banner_principal(self, obj):
        return format_html(f'<img src="{static('img/admin/home/banner.png')}" width="1000">')
    
    def preview_banner_pequeño(self, obj):
        return format_html(f'<img src="{static('img/admin/home/banner_medio.png')}" width="1000">')
    
    def preview_bento(self, obj):
        return format_html(f'<img src="{static('img/admin/home/bento.png')}" width="1000">')
    
    def preview_bento_estatico(self, obj):
        return format_html(f'<img src="{static('img/admin/home/bento_static.png')}" width="1000">')
    
    def preview_grilla_de_productos(self, obj):
        return format_html(f'<img src="{static('img/admin/home/grilla.png')}" width="1000">')

    def get_inlines(self, request, obj=None):
        if not obj:
            return []
        
        if obj.tipo == HomeSection.Tipo.BANNER_PRINCIPAL:
            return [HomeBannerInline]
        elif obj.tipo == HomeSection.Tipo.BANNER_MEDIO:
            return [HomeBannerMedioInline]
        elif obj.tipo == HomeSection.Tipo.GRILLA:
            return [HomeProductGridInline]
        elif obj.tipo == HomeSection.Tipo.BENTO:
            return [HomeCarouselBentoInline]
        elif obj.tipo == HomeSection.Tipo.STATIC_BENTO:
            return [HomeStaticBentoInline]

        return []

@admin.register(EventosPromociones)
class EventosPromocionesAdmin(ModelAdmin):
    list_display = ('nombre_evento', 'activo', 'fecha_inicio', 'fecha_fin')
    fieldsets = (
        (None, {
            'fields': ('nombre_evento', 'descripcion', 'activo', 'fecha_inicio', 'fecha_fin')
        }),
        ('Descuentos', {
            'fields': ('descuento_porcentaje', 'descuento_fijo')
        }),
        ('Opciones de visualización', {
            'fields': ('mostrar_en_inicio', 'logo')
        }),
    )

    def has_add_permission(self, request):
        if EventosPromociones.objects.count() > 0:
            return False
        return super().has_add_permission(request)

@admin.register(Tienda)
class TiendaAdmin(ModelAdmin):
    list_display = ('nombre_tienda', 'modo_stock', 'maximo_compra', 'mostrar_stock_en_front', 'divisa', 'valor_dolar', 'mantenimiento')
    readonly_fields = ('fecha_actualizacion_dolar', 'fecha_actualizacion_config')
    fieldsets = (
        ('Tu tienda', {
            'fields': ('nombre_tienda', 'color_primario','color_secundario','mantenimiento','borrar_cupon')
        }),
        ('Sistema de Stock',{
            'fields': ('modo_stock', 'maximo_compra', 'mostrar_stock_en_front')
        }),
        ('Divisas', {
            'fields': ('divisa', 'valor_dolar','fecha_actualizacion_dolar'),
        }),
    )
    conditional_fields = {
        'valor_dolar': "divisa == 'USD'",
        'maximo_compra': "modo_stock == 'libre'", 
        'fecha_actualizacion_dolar': "divisa == 'USD'",
        'mostrar_stock_en_front': "modo_stock != 'libre'",
    }