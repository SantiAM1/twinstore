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
from django.utils.html import format_html
from django.utils.timezone import localtime

# ───────────────────────────────
# ADMIN DE CONFIGURACION TIENDA
# ───────────────────────────────
@admin.register(Tienda)
class TiendaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_tienda",
        "modo_stock",
        "mostrar_stock_en_front",
        "borrar_cupon",
        "sitio_mantenimiento",
        "divisa",
        "valor_dolar_display",
    )

    readonly_fields = ("fecha_actualizacion_dolar", "fecha_actualizacion_config")

    fieldsets = (
        ("Configuración General", {
            "fields": ("nombre_tienda", "modo_stock","maximo_compra", "mostrar_stock_en_front", "borrar_cupon", "mantenimiento")
        }),
        ("Configuración de Divisa", {
            "fields": ("divisa", "valor_dolar", "fecha_actualizacion_dolar")
        }),
        ("Fechas de Actualización", {
            "fields": ("fecha_actualizacion_config",)
        }),
    )

    def valor_dolar_display(self, obj):
        if obj.divisa == Tienda.Divisas.USD:
            return obj.valor_dolar
        return ""
    valor_dolar_display.short_description = "Valor USD"

    def sitio_mantenimiento(self, obj):
        if not obj.mantenimiento:
            return format_html('<span style="color:#0f0;font-family:Arial, sans-serif;font-size:14px;display:flex;gap:0.5rem">Activo<img src="/static/admin/img/icon-yes.svg" alt="True"></span>')
        return format_html('<span style="color:#f00;font-family:Arial, sans-serif;font-size:14px;display:flex;gap:0.5rem">Mantenimiento<img src="/static/admin/img/icon-no.svg" alt="True"></span>')

# ───────────────────────────────
# ADMIN DE EVENTOS PROMOCION
# ───────────────────────────────
@admin.register(EventosPromociones)
class EventosPromocionesAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_evento",
        "rango_fechas",
        "activo",
        "tipo_descuento",
        "mostrar_en_inicio",
    )

    list_filter = (
        "activo",
        "mostrar_en_inicio",
        "fecha_inicio",
        "fecha_fin",
    )

    search_fields = ("nombre_evento", "descripcion")

    readonly_fields = ("slug",)

    fieldsets = (
        ("Información del Evento", {
            "fields": ("nombre_evento", "descripcion")
        }),
        ("Configuración de Fecha", {
            "fields": ("fecha_inicio", "fecha_fin", "activo")
        }),
        ("Descuento del Evento", {
            "fields": ("descuento_porcentaje", "descuento_fijo")
        }),
        ("Opciones de Visualización", {
            "fields": ("mostrar_en_inicio","logo")
        }),
    )

    def rango_fechas(self, obj):
        inicio = localtime(obj.fecha_inicio).strftime("%d/%m/%Y %H:%M")
        fin = localtime(obj.fecha_fin).strftime("%d/%m/%Y %H:%M")
        return f"{inicio} → {fin}"
    rango_fechas.short_description = "Vigencia"

    def tipo_descuento(self, obj):
        if obj.descuento_porcentaje:
            return format_html('<span style="color:#0a0;font-family:Arial, sans-serif;font-size:14px">-{}%</span>', obj.descuento_porcentaje)
        if obj.descuento_fijo:
            return format_html('<span style="color:#aaf;font-family:Arial, sans-serif;font-size:14px">-${}</span>', obj.descuento_fijo)
        return "-"
    tipo_descuento.short_description = "Descuento"


class HomeBannerInline(admin.TabularInline):
    model = HomeBanner
    extra = 1
    fields = ("imagen_desktop", "imagen_mobile", "url", "orden")
    ordering = ("orden",)
    classes = ['collapse']


class HomeBannerMedioInline(admin.TabularInline):
    model = HomeBannerMedio
    extra = 1
    fields = ("tipo", "titulo", "descripcion", "orden","svg")
    ordering = ("orden",)
    classes = ['collapse']


class HomeCategoryItemInline(admin.TabularInline):
    model = HomeCategoryItem
    extra = 1
    fields = ("categoria","subcategoria", "imagen", "tamano", "slide", "orden")
    ordering = ("slide", "orden")
    classes = ['collapse']

class HomeReseñasInline(admin.TabularInline):
    model = HomeReseñas
    extra = 1
    fields = ("titulo","subtitulo","calificaciones")
    classes = ['collapse']

# -------------------------------
#  ADMIN PRINCIPAL DE SECCIONES
# -------------------------------

@admin.register(HomeSection)
class HomeSectionAdmin(admin.ModelAdmin):
    list_display = ("orden", "tipo", "activo", "titulo")
    list_editable = ("orden", "activo")
    list_display_links = ("tipo",)
    ordering = ("orden",)
    search_fields = ("titulo", "subtitulo")

    inlines = [
        HomeBannerInline,
        HomeBannerMedioInline,
        HomeCategoryItemInline,
        HomeReseñasInline
    ]

    fieldsets = (
        ("Información General", {
            "fields": ("tipo", "activo", "orden")
        }),
    )