from django.contrib import admin
from .models import Venta,PagoRecibidoMP,ComprobanteTransferencia,EstadoPedido,Cupon,TicketDePago,VentaDetalle
from django.utils.html import format_html
from django.utils.timezone import localtime
from django.template.defaultfilters import date as date_filter
from .forms import EstadoPedidoForm

# Register your models here.

admin.site.register(PagoRecibidoMP)
admin.site.register(Cupon)
admin.site.register(TicketDePago)
admin.site.register(ComprobanteTransferencia)

class TicketPagoMixtoInline(admin.StackedInline):
    model = TicketDePago
    can_delete = False
    extra = 0
    classes = ['collapse']
    readonly_fields = ['estado','monto']

class ComprobanteTransferenciaInline(admin.StackedInline):
    model = ComprobanteTransferencia
    can_delete = False
    extra = 1
    classes = ['collapse']
    readonly_fields = ['file', 'fecha_subida']

class VentaDetalleInline(admin.StackedInline):
    model = VentaDetalle
    can_delete = False
    extra = 0
    classes = ['collapse']
    readonly_fields = ['producto','color','cantidad','precio_unitario','subtotal']
    fieldsets = (
        (None, {
            'fields': (
                'producto','color','cantidad','precio_unitario','subtotal'
            )
        }),
    )

class EstadoPedidoInline(admin.StackedInline):
    model = EstadoPedido
    form = EstadoPedidoForm
    can_delete = False
    extra = 0
    classes = ['collapse']
    ordering = ['-fecha']
    readonly_fields = ['render_estado_pedido']
    verbose_name_plural = "📝 Historial de estados del pedido"

    def get_fields(self, request, obj=None):
        return ['render_estado_pedido', 'estado', 'comentario']

    def render_estado_pedido(self, obj):
        color = "#f0ec23" if "(Servidor)" in obj.estado else "#ee4f2d"
        fecha_local = localtime(obj.fecha)
        fecha = date_filter(fecha_local, "d M Y H:i")
        comentario = obj.comentario or "—"
        comentario = comentario.replace('\n', '<br>')
        return format_html(
            f"""<p style="color:{color}">Comentario: {comentario}</p><p style="color:{color}">Fecha: {fecha}</p>"""
        )

    render_estado_pedido.short_description = "Informacion"

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    inlines = [EstadoPedidoInline]
    search_fields = ('merchant_order_id',)
    list_filter = ('estado', 'fecha_compra', 'requiere_revision')
    list_display = ('merchant_order_id', 'mostrar_nombre_apellido', 'total_compra', 'estado', 'fecha_compra','fecha_finalizado','requiere_revision')
    readonly_fields = ('merchant_order_id','datos_facturacion_expandible','fecha_compra','forma_de_pago','total_compra','fecha_finalizado')
    fieldsets = (
        (None, {
            'fields': (
                'merchant_order_id','total_compra', 'estado', 'forma_de_pago', 'fecha_finalizado','datos_facturacion_expandible'
            )
        }),
    )

    def get_inline_instances(self, request, obj=None):
        inline_instances = []
        inline_instances.append(VentaDetalleInline(self.model, self.admin_site))
        inline_instances.append(EstadoPedidoInline(self.model, self.admin_site))
        if obj and obj.forma_de_pago in ['transferencia','mixto']:
            inline_instances.append(ComprobanteTransferenciaInline(self.model, self.admin_site))
            if obj and obj.forma_de_pago == 'mixto':
                inline_instances.append(TicketPagoMixtoInline(self.model, self.admin_site))
        return inline_instances

    def mostrar_nombre_apellido(self, obj):
        if hasattr(obj, 'facturacion'):
            return f"{obj.facturacion.nombre} {obj.facturacion.apellido} | DNI/CUIT({obj.facturacion.dni_cuit})"
        return "-"

    def datos_facturacion_expandible(self, obj):
        if not hasattr(obj, 'facturacion'):
            return "Sin datos de facturación."
        
        f = obj.facturacion
        html = (
            '<div style="overflow-x: auto; max-width: 100%;">'
            '<table style="border-collapse: collapse; width: 100%; min-width: 800px;">'
            '<tr>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Nombre</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">DNI/CUIT</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Email</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Dirección</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Condición frente al IVA</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Teléfono</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Razón social</th>'
            '</tr>'
            f'<tr>'
            f'<td style="padding: 6px;">{f.nombre} {f.apellido}</td>'
            f'<td style="padding: 6px;">{f.dni_cuit}</td>'
            f'<td style="padding: 6px;">{f.email}</td>'
            f'<td style="padding: 6px;">{f.direccion} | {f.localidad} | CP{f.codigo_postal} | {f.get_provincia_display()}</td>'
            f'<td style="padding: 6px;">{f.get_condicion_iva_display()}</td>'
            f'<td style="padding: 6px;">{f.telefono}</td>'
            f'<td style="padding: 6px;">{f.razon_social or " "}</td>'
            f'</tr>'
            '</table>'
            '</div>'
        )
        return format_html(html)

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return False  # no permitir borrar desde la lista
        return obj.estado in ['finalizado', 'arrepentido']

    mostrar_nombre_apellido.short_description = "Cliente"
    datos_facturacion_expandible.short_description = "Datos de facturación"