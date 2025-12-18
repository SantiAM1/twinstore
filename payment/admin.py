from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Venta,PagoRecibidoMP,ComprobanteTransferencia,EstadoPedido,Cupon,TicketDePago,VentaDetalle
from users.models import DatosFacturacion

from unfold.admin import ModelAdmin,TabularInline,StackedInline
from unfold.decorators import display
from unfold.sections import TableSection
from unfold.paginator import InfinitePaginator

class DatosFacturacionInline(StackedInline):
    model = DatosFacturacion
    extra = 0
    tab = True
    readonly_fields = ('nombre','apellido','razon_social','dni_cuit','condicion_iva','provincia','localidad','direccion','codigo_postal','telefono','email')

class TicketDePagoInline(TabularInline):
    model = TicketDePago
    extra = 0
    tab = True

class ComprobanteTransferenciaInline(TabularInline):
    model = ComprobanteTransferencia
    extra = 0
    tab = True

class EstadoPedidoInline(TabularInline):
    model = EstadoPedido
    extra = 0
    tab = True

class VentaDetalleInline(TabularInline):
    model = VentaDetalle
    extra = 0
    tab = True
    readonly_fields = ('portada','producto','cantidad','color','precio_unitario','subtotal')
    fields = ('portada','producto','cantidad','color','precio_unitario','subtotal')
    hide_title = True

    def portada(self, instance):
        return format_html(f"<img src='{instance.imagen_url}' width='50' height='50' style='object-fit: cover;border-radius: 5px;' />")

@admin.register(Cupon)
class CuponAdmin(ModelAdmin):
    fields = ('codigo','descuento','creado')
    readonly_fields = ('codigo','creado')

class DetalleCompraSection(TableSection):
    verbose_name = _("Detalle de compra")
    height = 300
    related_name = "detalles"
    fields = ["portada","producto", "cantidad","color","precio_unitario","subtotal"]

    # Custom field
    def portada(self, instance):
        return format_html(f"<img src='{instance.imagen_url}' width='50' height='50' style='object-fit: cover;border-radius: 5px;' />")

@admin.register(Venta)
class VentaAdmin(ModelAdmin):
    list_display = ('usuario','total_compra','fecha_compra','show_estado','forma_de_pago','merchant_order_id','fecha_finalizado','requiere_revision')
    list_filter = ('estado','forma_de_pago','fecha_compra')
    search_fields = ('usuario__username','merchant_order_id')
    readonly_fields = ('pagos','fecha_compra','merchant_order_id','forma_de_pago','usuario','total_compra','fecha_finalizado')
    list_sections = [
        DetalleCompraSection,
    ]

    inlines = [VentaDetalleInline,DatosFacturacionInline, ComprobanteTransferenciaInline, EstadoPedidoInline,TicketDePagoInline]

    fieldsets = (
        (None, {
            'fields': ('usuario','forma_de_pago','merchant_order_id','total_compra','estado','requiere_revision')
        }),
        ('Fechas', {
            'fields': ('fecha_compra','fecha_finalizado'),
        }),
    )

    @display(
        description="Estado",
        ordering="estado",
        label={
            Venta.Estado.PENDIENTE: "warning",
            Venta.Estado.CONFIRMADO: "success",
            Venta.Estado.RECHAZADO: "danger",
            Venta.Estado.FINALIZADO: "info",
            Venta.Estado.ARREPENTIDO: "danger",
            Venta.Estado.ENVIADO: "primary",
        }
    )
    def show_estado(self, obj):
        return obj.estado, obj.get_estado_display()

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related('detalles','detalles__producto')
            )
    
    def has_add_permission(self, request):
        return False