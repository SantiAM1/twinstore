from django.contrib import admin
from unfold.admin import ModelAdmin,TabularInline, StackedInline


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
    list_display = ('public_key', 'access_token', 'modo_sandbox')

    def has_add_permission(self, request):
        return True if MercadoPagoConfig.objects.count() == 0 else False

@admin.register(DatosBancarios)
class DatosBancariosAdmin(ModelAdmin):
    list_display = ('banco', 'numero_cuenta', 'alias','titular_cuenta')

    def has_add_permission(self, request):
        return True if MercadoPagoConfig.objects.count() == 0 else False

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
                'producto', 
                'categoria', 
                'subcategoria', 
                'marca'
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

class HomeBannerMedioInline(StackedInline):
    model = HomeBannerMedio
    extra = 1
    max_num = 3

    fieldsets = (
        (None, {
            'fields': ('tipo','svg','titulo','descripcion','orden')
        }),
    )

class HomeProductGridInline(StackedInline):
    model = HomeProductGrid
    extra = 1
    max_num = 1

class HomeBannerInline(StackedInline):
    model = HomeBanner
    extra = 1
    max_num = 5

@admin.register(HomeSection)
class HomeSectionAdmin(ModelAdmin):
    list_display = ['orden', 'tipo', 'activo']
    
    fieldsets = (
        (None, {
            'fields': ('orden', 'tipo', 'titulo', 'subtitulo','activo')
        }),
    )

    conditional_fields = {
        'titulo': "['grilla', 'bento', 'static_bento'].includes(tipo)",
        'subtitulo': "['grilla', 'bento', 'static_bento'].includes(tipo)",
    }

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
            'fields': ('nombre_tienda', 'mantenimiento','borrar_cupon')
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