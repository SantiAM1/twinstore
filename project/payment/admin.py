from django.contrib import admin
from .models import HistorialCompras,PagoRecibidoMP,ComprobanteTransferencia
# Register your models here.
admin.site.register(HistorialCompras)
admin.site.register(PagoRecibidoMP)

@admin.register(ComprobanteTransferencia)
class ComprobanteAdmin(admin.ModelAdmin):
    readonly_fields = ['historial']
    list_display = ['historial','fecha_subida', 'aprobado']
    list_filter = ['aprobado']
    search_fields = ['historial__merchant_order_id']
