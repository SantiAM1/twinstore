from django.contrib import admin
from .models import HistorialCompras,PagoRecibidoMP,ComprobanteTransferencia
from django.utils.html import format_html, format_html_join
from django.urls import reverse
# Register your models here.

admin.site.register(PagoRecibidoMP)

class ComprobanteTransferenciaInline(admin.StackedInline):
    model = ComprobanteTransferencia
    can_delete = False
    extra = 0
    classes = ['collapse']
    readonly_fields = ['file', 'fecha_subida']

@admin.register(HistorialCompras)
class HistorialComprasAdmin(admin.ModelAdmin):
    list_display = ('merchant_order_id', 'mostrar_nombre_apellido', 'total_compra', 'estado', 'fecha_compra','fecha_finalizado')
    readonly_fields = ('merchant_order_id','detalle_productos','datos_facturacion_expandible','fecha_compra','fecha_finalizado','forma_de_pago','total_compra')
    fieldsets = (
        (None, {
            'fields': (
                'detalle_productos','merchant_order_id','total_compra', 'estado', 'forma_de_pago', 'fecha_finalizado','datos_facturacion_expandible'
            )
        }),
    )

    def get_inline_instances(self, request, obj=None):
        inline_instances = []
        if obj:  # Solo en vista de edición/detalle
            if obj.forma_de_pago == 'transferencia':
                # Aunque no exista comprobante aún, mostramos igual si queremos permitir verlo como readonly
                inline_instances.append(ComprobanteTransferenciaInline(self.model, self.admin_site))
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
            '<table style="border-collapse: collapse; width: 100%;">'
            '<tr>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Nombre</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">DNI/CUIT</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Email</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Dirección</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Tipo de factura</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Telefono</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Razon social</th>'
            '</tr>'
            f'<tr>'
            f'<td style="padding: 6px;">{f.nombre} {f.apellido}</td>'
            f'<td style="padding: 6px;">{f.dni_cuit}</td>'
            f'<td style="padding: 6px;">{f.email}</td>'
            f'<td style="padding: 6px;">{f.calle} {f.calle_detail or ''}, {f.ciudad or '-'} CP({f.codigo_postal or '-'}), {f.get_provincia_display()}</td>'
            f'<td style="padding: 6px;">{f.get_tipo_factura_display()}</td>'
            f'<td style="padding: 6px;">{f.telefono or '-'}</td>'
            f'<td style="padding: 6px;">{f.razon_social or '-'}</td>'
            f'</tr>'
            '</table>'
            )
        return format_html(html)

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return False  # no permitir borrar desde la lista
        return obj.estado in ['finalizado', 'arrepentido']

    def detalle_productos(self, obj):
        if not obj.productos:
            return "Sin productos."
        html = '<table style="border-collapse: collapse; width: 100%;">'
        html += (
            '<tr>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">SKU</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Producto</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Cantidad</th>'
            '<th style="padding: 6px; border-bottom: 1px solid #ddd;">Subtotal</th>'
            '</tr>'
        )
        for p in obj.productos:
            html += (
                f'<tr>'
                f'<td style="padding: 6px;">{p["sku"]}</td>'
                f'<td style="padding: 6px;">{p["nombre"]}</td>'
                f'<td style="padding: 6px;">{p["cantidad"]}</td>'
                f'<td style="padding: 6px;">${p["subtotal"]:,.2f}</td>'
                f'</tr>'
            )
        html += '</table>'
        return format_html(html)

    detalle_productos.short_description = "Detalle de compra"
    mostrar_nombre_apellido.short_description = "Cliente"
    datos_facturacion_expandible.short_description = "Datos de facturación"