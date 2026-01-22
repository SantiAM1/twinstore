from datetime import timedelta,datetime
from decimal import Decimal

from django.http import HttpRequest
from django.utils import timezone
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.db.models import QuerySet,TimeField,DateField,Count,Sum,OuterRef, Subquery,F,Sum,Value
from django.db.models.functions import TruncHour,TruncDay,TruncMonth,TruncYear,Coalesce
from core.utils import get_configuracion_tienda
from payment.models import Venta,VentaDetalle
from payment.templatetags.custom_filters import formato_pesos
from products.models import MovimientoStock,LoteStock,Producto
from django.contrib.auth import get_user_model

User = get_user_model()

INFO = "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400"
DANGER = "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400"
WARNING = "bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400"
SUCCESS = "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400"
PRIMARY = "bg-primary-100 text-primary-700 dark:bg-primary-500/20 dark:text-primary-400"
DEFAULT = "bg-base-100 text-base-700 dark:bg-base-500/20 dark:text-base-200"

def dashboard_tabs(periodo: str) -> list[dict]:
    tabs_data = [
        {"name": "Últimos 30 días", "param": "30dias", "active": periodo == "30dias"},
        {"name": "Último Año", "param": "1año", "active": periodo == "1año"},
        {"name": "Ultimas 24 horas", "param": "24horas", "active": periodo == "24horas"},
        {"name": "Siempre", "param": "siempre", "active": periodo == "siempre"},
    ]
    return tabs_data

def filtro_fechas(request: HttpRequest) -> tuple:
    periodo = request.GET.get('param', '30dias')

    ahora = timezone.localtime()
    fecha_inicio = None

    if periodo == '24horas':
        fecha_inicio = ahora - timedelta(hours=24)
        fecha_anterior = ahora - timedelta(hours=48)
    elif periodo == '30dias':
        fecha_inicio = ahora - timedelta(days=30)
        fecha_anterior = ahora - timedelta(days=60)
    elif periodo == '1año':
        fecha_inicio = ahora - timedelta(days=365)
        fecha_anterior = ahora - timedelta(days=730)
    elif periodo == 'siempre':
        fecha_inicio = None
        fecha_anterior = None
    
    return periodo, fecha_inicio,fecha_anterior

def ultimos_pedidos(ventas: Venta) -> dict:
    return {
            "height": 300,
            "headers": ["Orden", "Total","Estado"],
            "rows": [
                [format_html("<a href=\"{}\" style='color:var(--color-primary-500); font-weight: 400;'>#{}</a>", reverse_lazy("admin:payment_venta_change", args=[venta.id]), venta.merchant_order_id), formato_pesos(venta.total_compra), label_estado(venta)] for venta in ventas
            ]
        }

def label_estado(venta: Venta) -> str:
    if venta.estado == 'confirmado':
        classes = SUCCESS
    elif venta.estado == 'pendiente':
        classes = WARNING
    elif venta.estado == 'rechazado' or venta.estado == 'arrepentido':
        classes = DANGER
    elif venta.estado == 'enviado':
        classes = PRIMARY
    elif venta.estado == 'finalizado':
        classes = INFO
    else:
        classes = DEFAULT
    return format_html(
        f'<span class="inline-block font-semibold h-6 leading-6 px-2 rounded-default text-[11px] uppercase whitespace-nowrap {classes}">{venta.get_estado_display()}</span>'
        )

def kpi_dashboard(request, fecha_inicio: timedelta, fecha_anterior: timedelta, ventas_all: QuerySet[Venta]) -> dict[str, dict[str, str | float]]:
    estados_validos = [
        Venta.Estado.CONFIRMADO,
        Venta.Estado.ENVIADO,
        Venta.Estado.FINALIZADO,
        Venta.Estado.LISTO_PARA_RETIRAR,
    ]
    config = get_configuracion_tienda(request)
    # --- 1. Filtrado de Ventas y Usuarios ---
    if fecha_inicio:
        ventas = ventas_all.filter(
            fecha_compra__gte=fecha_inicio,
            estado__in=estados_validos
            )
        ventas_anterior = ventas_all.filter(
            fecha_compra__gte=fecha_anterior,
            fecha_compra__lt=fecha_inicio,
            estado__in=estados_validos
            )
        usuarios_count = User.objects.filter(date_joined__gte=fecha_inicio).count()
        usuarios_anterior = User.objects.filter(date_joined__gte=fecha_anterior, date_joined__lt=fecha_inicio).count()
        comparacion_valida = True
    else:
        ventas = ventas_all.filter(estado__in=estados_validos)
        ventas_anterior = []
        usuarios_count = User.objects.all().count()
        usuarios_anterior = 0
        comparacion_valida = False

    # --- 2. Cálculos de Ingresos y Órdenes ---
    total_ventas = ventas.count()
    total_ventas_anterior = ventas_anterior.count() if comparacion_valida else 0

    total_ingresos = 0
    total_ingresos_anterior = 0
    
    if config['modo_stock'] == 'estricto':
        margen = calcular_margen_de_ganancia(ventas)
        margen_anterior = calcular_margen_de_ganancia(ventas_anterior) if comparacion_valida else {}
    
    total_ingresos = ventas.aggregate(Sum('total_compra'))['total_compra__sum'] or 0
        
    if comparacion_valida:
        total_ingresos_anterior = ventas_anterior.aggregate(Sum('total_compra'))['total_compra__sum'] or 0

    # --- 3. Cálculos del Ticket Promedio (AOV) ---
    
    # Ticket Promedio Actual
    ticket_promedio_actual = total_ingresos / total_ventas if total_ventas > 0 else 0
    
    # Ticket Promedio Anterior
    if total_ventas_anterior > 0 and comparacion_valida:
        ticket_promedio_anterior = total_ingresos_anterior / total_ventas_anterior
    else:
        ticket_promedio_anterior = 0

    return {
        "ingresos":{
            "value": formato_pesos(total_ingresos),
            "title": "Ingresos totales",
            "pasado": porcentaje(total_ingresos, total_ingresos_anterior),
            "icon": "monetization_on",
        },
        "ganancias":{
            "value": formato_pesos(margen['margen_ganancia_total'] or 0),
            "title": "Ganancias generadas",
            "pasado": porcentaje(margen.get('margen_ganancia_total') or 0, margen_anterior.get('margen_ganancia_total') or 0),
            "icon": "trending_up",
        } if config['modo_stock'] == 'estricto' else {},
        "ordenes": {
            "value": total_ventas,
            "title": "Órdenes realizadas",
            "pasado": porcentaje(total_ventas, total_ventas_anterior),
            "icon": "shopping_cart",
        },
        "usuarios": {
            "value": usuarios_count,
            "title": "Usuarios nuevos",
            "pasado": porcentaje(usuarios_count, usuarios_anterior),
            "icon": "person",
        },
        "ticket": {
            "value": formato_pesos(ticket_promedio_actual),
            "title": "Ticket Promedio",
            "pasado": porcentaje(ticket_promedio_actual, ticket_promedio_anterior) if comparacion_valida else 0.0,
            "icon": "receipt_long",
        },
    }

def porcentaje(actual: float, anterior: float) -> float:
    if anterior == 0:
        if actual > 0:
            return 999.9

        return 0.0
    return round(((actual - anterior) / anterior) * 100, 1)

def buttons_chart(request: HttpRequest) -> dict[str, dict[str, str]]:
    return {
        "ingresos":{
            "href": build_path(request,param='ingresos'),
            "label": "Ingresos",
        },
        "ventas": {
            "href": build_path(request,param='ventas'),
            "label": "Cantidad de ventas",
        },
        "usuarios": {
            "href": build_path(request,param='usuarios'),
            "label": "Usuarios registrados",
        },
        "ticket": {
            "href": build_path(request,param='ticket'),
            "label": "Ticket Promedio",
        },
    }

def calcular_margen_de_ganancia(ventas_qs):
    # Paso 1: Obtener el precio unitario de VentaDetalle (Precio de Venta) 
    #         para cada movimiento. Usamos Subquery.
    
    # Buscamos el precio unitario en VentaDetalle que corresponda a este MovimientoStock
    precio_venta_unitario = VentaDetalle.objects.filter(
        venta=OuterRef('venta_id'),
        producto=OuterRef('producto_id'),
    ).values('precio_unitario')[:1] 
    
    # Paso 2: Filtrar y Anotar los Movimientos con el Precio de Venta
    movimientos_con_precios = MovimientoStock.objects.filter(
        tipo=MovimientoStock.Tipo.SALIDA,
        venta__in=ventas_qs
    ).annotate(
        costo_unitario_mov=F('lote__costo_unitario'),
        precio_venta_unitario=Subquery(precio_venta_unitario) 
        
    ).exclude(
        precio_venta_unitario__isnull=True # Descartar si no encontramos precio de venta
    ).select_related('lote') # Optimización

    # Paso 3: Calcular el Margen (Precio de Venta - Costo) y Sumar los Totales
    margen_qs = movimientos_con_precios.annotate(
        # Margen por unidad: (Precio Venta - Costo)
        margen_unitario=F('precio_venta_unitario') - F('costo_unitario_mov'),
        
        # Ganancia total por movimiento: Margen unitario * Cantidad
        ganancia_total_mov=F('margen_unitario') * F('cantidad')
    )

    # Paso 4: Sumar la ganancia total
    resultados = margen_qs.aggregate(
        costo_total_ventas=Sum(F('costo_unitario_mov') * F('cantidad')),
        ingreso_total_ventas=Sum(F('precio_venta_unitario') * F('cantidad')),
        margen_ganancia_total=Sum('ganancia_total_mov')
    )
    
    # Resultados contiene los totales calculados 100% en la base de datos
    return resultados

def build_path(request: HttpRequest, param: str) -> str:
    base_url = request.path
    query_params = request.GET.copy()
    query_params['line_type'] = param
    return f"{base_url}?{query_params.urlencode()}"

def bar_chart_data(periodo: str,type: str = "ventas",**kwargs) -> tuple[dict[str | int, int],str]:
    # Obtenemos el formato para el label
    format = format_date(periodo)

    # Obtenemos la query correspondiente
    if type == "ventas":
        query = ventas_query(periodo)
        label = "Cantidad de Ventas"
    elif type == "ingresos":
        query = ingresos_query(periodo)
        label = "Ingresos Totales"
    elif type == "usuarios":
        query = usuarios_query(periodo)
        label = "Usuarios Nuevos"
    elif type == "ticket":
        query = ticket_promedio_query(periodo)
        label = "Ticket Promedio"
    
    # Generamos los labels
    labels = label_generator(**kwargs)

    # Rellenamos los datos en los labels
    for item in query:
        field = item['data'].strftime(format)
        try:
            labels[field] += float(item['total'])
        except ValueError:
            labels[field] += item['total']
    
    return labels, label

def ticket_promedio_query(periodo:str = "30dias"):
    annotated, delta = annotated_delta(periodo)
    if delta is None:
        return (
            Venta.objects
            .annotate(data=annotated)
            .values('data')
            .annotate(total=Sum('total_compra') / Count('id'))
            .order_by('data')
            )
    
    ticket_promedio_agregado = (
        Venta.objects
        .filter(fecha_compra__gte=timezone.localtime() - delta)
        .annotate(data=annotated)
        .values('data')
        .annotate(total=Sum('total_compra') / Count('id'))
        .order_by('data')
    )

    return ticket_promedio_agregado

def usuarios_query(periodo:str = "30dias"):
    annotated, delta = annotated_delta(periodo, field="date_joined")
    if delta is None:
        return (
            User.objects
            .annotate(data=annotated)
            .values('data')
            .annotate(total=Count('id'))
            .order_by('data')
            )
    
    usuarios_agregados = (
        User.objects
        .filter(date_joined__gte=timezone.localtime() - delta)
        .annotate(data=annotated)
        .values('data')
        .annotate(total=Count('id'))
        .order_by('data')
    )

    return usuarios_agregados

def ingresos_query(periodo:str = "30dias"):
    annotated, delta = annotated_delta(periodo)
    if delta is None:
        return (
            Venta.objects
            .annotate(data=annotated)
            .values('data')
            .annotate(total=Sum('total_compra'))
            .order_by('data')
            )
    
    ingresos_agregados = (
        Venta.objects
        .filter(fecha_compra__gte=timezone.localtime() - delta)
        .annotate(data=annotated)
        .values('data')
        .annotate(total=Sum('total_compra'))
        .order_by('data')
    )

    return ingresos_agregados
    
def ventas_query(periodo:str = "30dias"):
    annotated, delta = annotated_delta(periodo)
    if delta is None:
        return (
            Venta.objects
            .annotate(data=annotated)
            .values('data')
            .annotate(total=Count('id'))
            .order_by('data')
            )
    
    ventas_agregadas = (
        Venta.objects
        .filter(fecha_compra__gte=timezone.localtime() - delta)
        .annotate(data=annotated)
        .values('data')
        .annotate(total=Count('id'))
        .order_by('data')
    )

    return ventas_agregadas

def annotated_delta(periodo:str = "30dias",field:str = "fecha_compra") -> tuple:
    if periodo == "24horas":
        annotated = TruncHour(field, output_field=TimeField())
        delta = timedelta(hours=24)

    elif periodo == "30dias":
        annotated = TruncDay(field, output_field=DateField())
        delta = timedelta(days=30)

    elif periodo == "1año":
        annotated = TruncMonth(field, output_field=DateField())
        delta = timedelta(days=365)

    elif periodo == "siempre":
        annotated = TruncYear(field, output_field=DateField())
        delta = None

    return annotated, delta

def format_date(periodo: str) -> str:
    if periodo == "24horas":
        return "%H:%M"
    elif periodo == "30dias":
        return "%d/%m"
    elif periodo == "1año":
        return "%m/%Y"
    else:
        return "%Y"

def label_generator(hours: int = None, days:int = None, month: int = None) -> dict[int | str, int]:
    label = []
    if days:
        for i in range(days):
            label.append((timezone.localtime() - timezone.timedelta(days=i)).strftime("%d/%m"))

    elif hours:
        for i in range(hours):
            label.append((timezone.localtime().replace(minute=0, second=0, microsecond=0) - timezone.timedelta(hours=i)).strftime("%H:%M"))
    
    elif month:
        for i in range(month):
            label.append((timezone.localtime() - timezone.timedelta(days=i*30)).strftime("%m/%Y"))
    else:
        start_year = timezone.localtime().year
        end_year = start_year - 5
        
        label.extend(str(year) for year in range(start_year, end_year, -1))
    
    label.reverse()
    return dict.fromkeys(label,0)

def kpi_2_dashboard():
    inventario_total = LoteStock.objects.aggregate(total_inventario=Sum(F('costo_unitario') * F('cantidad_disponible')))
    cantidad_productos = LoteStock.objects.filter(cantidad_disponible__gt=0).count()
    pedidos_pendientes = Venta.objects.filter(estado=Venta.Estado.PENDIENTE).count()

    return  {
        "inventario_total":{
            "title": "Valor total del inventario",
            "value": formato_pesos(inventario_total['total_inventario'] or 0),
            "icon": "inventory",
            "footer": "Calculado según el costo de adquisición",
        },
        "productos_en_inventario":{
            "title": "Productos en inventario",
            "value": cantidad_productos,
            "icon": "storefront",
            "footer": "Número de productos con stock disponible",
        },
        "pedidos_pendientes":{
            "title": "Pedidos pendientes",
            "value": pedidos_pendientes,
            "icon": "pending_actions",
            "footer": "Número de pedidos pendientes",
        },
        "tasa_conversion":{
            "title": "Tasa de conversión",
            "value": "N/A",
            "icon": "insights",
            "footer": "Próximamente disponible",
        }
    }

def subcategorias_rentables():
    ventas = VentaDetalle.objects.filter(
                venta__estado=Venta.Estado.CONFIRMADO
            ).values(
                'producto__sub_categoria__nombre'
            ).annotate(
                subcategoria_nombre=F('producto__sub_categoria__nombre'),
                total_vendido=Sum(F('precio_unitario') * F('cantidad')),
            ).values(
                'subcategoria_nombre', 'total_vendido'
            ).order_by('-total_vendido')[:5]
    
    return ventas

def prod_menos_stock_table() -> dict:
    productos = prod_menos_stock()
    return {
            "height": 300,
            "headers": ["SKU", "Nombre", "Stock Disponible"],
            "rows": [
                [format_html("<a href=\"{}\" style='color:var(--color-primary-500); font-weight: 400;'>#{}</a>", reverse_lazy("admin:products_producto_change", args=[producto['id']]), producto['sku']), producto['nombre'], label_stock(producto['total_stock'])] for producto in productos
            ]
        }

def prod_menos_stock() -> dict[str, str | int]:
    productos_bajo_stock = Producto.objects.annotate(
        total_stock = Coalesce(
            Sum('ingresos_stock__lotes__cantidad_disponible'),
            Value(0)
            )
        ).values(
            'sku','nombre','total_stock','id'
        ).order_by(
            "total_stock"
        )[:8]

    return productos_bajo_stock

def label_stock(stock: int) -> str:
    if stock > 5:
        classes = SUCCESS
        msg = "En stock"
    elif stock > 0:
        classes = WARNING
        msg = "Bajo stock"
    elif stock == 0:
        classes = DANGER
        msg = "Sin stock"
    else:
        classes = DEFAULT
    return format_html(
        f'<span class="inline-block font-semibold h-6 leading-6 px-2 rounded-default text-[11px] uppercase whitespace-nowrap {classes}">{msg}</span>'
        )

def ultimas_reseñas():
    from products.models import ReseñaProducto

    reseñas = ReseñaProducto.objects.select_related('producto', 'usuario').order_by('-creado_en')[:5]
    return reseñas