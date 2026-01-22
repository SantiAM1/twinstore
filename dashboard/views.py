from payment.models import Venta
from django.http import HttpRequest
from products.models import AjusteStock

from .utils import (
    dashboard_tabs,
    filtro_fechas,
    ultimos_pedidos,
    kpi_dashboard,
    buttons_chart,
    kpi_2_dashboard,
    prod_menos_stock_table,
    ultimas_reseñas
)


def dashboard_callback(request: HttpRequest, context: dict) -> dict:
    # imports basicos
    line_type = request.GET.get('line_type','ingresos')
    periodo, fecha_inicio,fecha_anterior = filtro_fechas(request)
    tabs_data = dashboard_tabs(periodo)
    ventas_all = Venta.objects.all()
    
    kpi_data = kpi_dashboard(request,fecha_inicio, fecha_anterior,ventas_all)

    buttons_chart_data = buttons_chart(request)

    kpi_macro = kpi_2_dashboard()
    
    last_rewiews = ultimas_reseñas()

    context.update({
        "tabs": tabs_data,
        "periodo_actual": periodo,
        "line_type": line_type,
        "kpi_list": kpi_data,
        "kpi_macro": kpi_macro,
        "buttons_chart": buttons_chart_data,
        "table_data": ultimos_pedidos(ventas_all.order_by('-fecha_compra')[:6]),
        "prod_menos_stock": prod_menos_stock_table(),
        "ultimas_resenas": last_rewiews,
    })

    return context

def ajuste_stock(request: HttpRequest) -> int:
    count = AjusteStock.objects.filter(resuelto=False).count()
    return count

def ventas_verificacion(request: HttpRequest) -> int:
    count = Venta.objects.filter(requiere_revision=True).count()
    return count

def environment_callback(request: HttpRequest) -> list[str]:
    if request.tenant.schema_name == 'public':
        return []
    from core.utils import get_configuracion_tienda
    
    config = get_configuracion_tienda(request)

    return ["Mantenimiento", "danger"] if config['mantenimiento'] else ["Sitio Activo", "success"]