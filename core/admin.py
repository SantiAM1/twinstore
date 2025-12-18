from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    Tienda,
    EventosPromociones,
    HomeSection,
    HomeBannerMedio,
    HomeCategoryItem,
    HomeBanner,
    HomeReseñas
)

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