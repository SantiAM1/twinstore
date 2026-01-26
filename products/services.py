from django.db import transaction
from django.db.models import Sum
from .models import LoteStock, MovimientoStock, AjusteStock
from payment.models import Venta,VentaDetalle

def gestionar_stock_venta(venta: Venta) -> bool:
    """
    Gestiona el descuento de stock para una venta confirmada.
    * Retorna True si se pudo descontar todo el stock correctamente.
    * Retorna False si falta stock para algún producto (no se descuenta nada).
    """
    with transaction.atomic():
        # 1. Fase de Verificación (Check Phase)
        # Verificamos si hay stock suficiente para TODOS los productos. Si falta alguno, no descontamos nada.
        faltantes = []

        for detalle in venta.detalles.all():
            detalle: VentaDetalle
            producto = detalle.producto
            variante = detalle.variante
            cantidad_requerida = detalle.cantidad
            
            filtros = {
                'ingreso__producto': producto,
                'cantidad_disponible__gt': 0
            }
            if variante:
                filtros['ingreso__variante'] = variante
            
            stock_disponible = LoteStock.objects.filter(**filtros).select_for_update().aggregate(
                total=Sum('cantidad_disponible')
            )['total'] or 0
            
            if stock_disponible < cantidad_requerida:
                faltantes.append({
                    'producto': producto,
                    'variante': variante,
                    'cantidad_faltante': cantidad_requerida - stock_disponible
                })

        if faltantes:
            for f in faltantes:
                AjusteStock.objects.create(
                    venta=venta,
                    producto=f['producto'],
                    variante=f['variante'],
                    cantidad_faltante=f['cantidad_faltante']
                )
            return False

        # 2. Fase de Descuento (Deduction Phase)
        # Se descuenta el stock de los productos, lote por lote (FIFO)

        for detalle in venta.detalles.all():
            producto = detalle.producto
            variante = detalle.variante
            cantidad_pendiente = detalle.cantidad
            
            filtros = {
                'ingreso__producto': producto,
                'cantidad_disponible__gt': 0
            }

            if variante:
                filtros['ingreso__variante'] = variante
            
            lotes = LoteStock.objects.filter(**filtros).select_for_update().order_by('fecha_ingreso')
            
            for lote in lotes:
                if cantidad_pendiente <= 0:
                    break
                
                cantidad_a_descontar = min(lote.cantidad_disponible, cantidad_pendiente)
                
                # Actualizamos lote
                lote.cantidad_disponible -= cantidad_a_descontar
                lote.save()
                
                # Creamos movimiento
                MovimientoStock.objects.create(
                    producto=producto,
                    variante=variante,
                    tipo=MovimientoStock.Tipo.SALIDA,
                    cantidad=cantidad_a_descontar,
                    lote=lote,
                    venta=venta
                )
                
                cantidad_pendiente -= cantidad_a_descontar
                
        return True