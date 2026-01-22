from functools import wraps
import json
from collections import defaultdict

from django.http import HttpRequest
from django.db.models import Count,QuerySet
from django.conf import settings
from django.core.cache import cache

from core.models import EventosPromociones
from payment.templatetags.custom_filters import formato_pesos

from import_export import resources
from import_export.widgets import ManyToManyWidget, ForeignKeyWidget,DecimalWidget
from import_export import fields

from products.models import (
    Categoria,
    Atributo,
    Producto,
    SubCategoria,
    Etiquetas,
    Marca,
    ColorProducto,
    Proveedor,
    IngresoStock
)

import locale
from decimal import Decimal

try:
    locale.setlocale(locale.LC_NUMERIC, 'es_AR.UTF-8') 
except locale.Error:
    locale.setlocale(locale.LC_NUMERIC, 'es_ES.UTF-8') 

class DecimalTwoPlacesWidget(DecimalWidget):
    
    def render(self, value, obj=None, **kwargs):
        if value is None:
            return ""
        
        if not isinstance(value, Decimal):
             value = Decimal(value)

        return locale.format_string("%.2f", value, grouping=True)

class IngresoStockResource(resources.ModelResource):
    producto = fields.Field(
        column_name='Nombre Producto',
        attribute='producto',
        widget=ForeignKeyWidget(Producto, field='nombre')
    )
    producto_color = fields.Field(
        column_name='Color Producto',
        attribute='producto_color',
        widget=ForeignKeyWidget(ColorProducto, field='nombre')
    )
    proveedor = fields.Field(
        column_name='Nombre Proveedor',
        attribute='proveedor',
        widget=ForeignKeyWidget(Proveedor, field='nombre')
    )

    costo_unitario = fields.Field(
        column_name='Costo Unitario',
        attribute='costo_unitario',
        widget=DecimalTwoPlacesWidget()
        )

    def before_save_instance(self, instance, row, **kwargs):
        print(instance, row, kwargs)
        request = kwargs.get('request','')
        if request and hasattr(request, 'user'):
            instance.creado_por = request.user

    def skip_row(self, instance, original, row,*args, **kwargs):
        if instance.fecha_ingreso is not None:
            return True 
        return False

    class Meta:
        model = IngresoStock
        import_id_fields = ('id',) 
        
        fields = (
            'id',
            'producto',
            'producto_color',
            'costo_unitario',
            'cantidad',
            'proveedor',
        )

        exclude = ('fecha_ingreso', 'creado_por')

class ProductoResource(resources.ModelResource):
    sub_categoria = fields.Field(
        column_name='Sub Categoría',
        attribute='sub_categoria',
        widget=ForeignKeyWidget(SubCategoria, field='nombre')
    )
    marca = fields.Field(
        column_name='Marca',
        attribute='marca',
        widget=ForeignKeyWidget(Marca, field='nombre')
    )

    evento = fields.Field(
        column_name='Nombre Evento',
        attribute='evento',
        widget=ForeignKeyWidget(EventosPromociones, field='nombre_evento')
    )
    
    etiquetas = fields.Field(
        column_name='Etiquetas (Separadas por coma)', 
        attribute='etiquetas', 
        widget=ManyToManyWidget(Etiquetas, field='nombre', separator=',')
    )

    precio_divisa = fields.Field(
        column_name='Precio USD/ARS',
        attribute='precio_divisa',
        widget=DecimalTwoPlacesWidget()
    )

    nombre = fields.Field(
        column_name='Nombre Producto',
        attribute='nombre'
    )

    def skip_row(self, instance, original, row,*args, **kwargs):
        if instance.slug is None:
            return True
        return False

    class Meta:
        model = Producto
        import_id_fields = ('nombre',) 
        
        fields = (
            'nombre', 
            'sub_categoria',
            'marca', 
            'precio_divisa', 
            'descuento', 
            'inhabilitar',
            'etiquetas',
            'evento'
        )

        exclude = ('id', 'created_at', 'updated_at')

def inject_categorias_subcategorias(view_func):
    """
    Decorador que envia a la vista las categorias y las subcategorias.
    Se utiliza en prodGrid.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from core.utils import gen_cache_key
        CAT_CACHE_KEY = gen_cache_key('categoty_subcat', request)
        categorias_data = cache.get(CAT_CACHE_KEY)
        if not categorias_data:
            categorias = Categoria.objects.prefetch_related('subcategorias').all()
            categorias_data = [
                {
                    'nombre': c.nombre,
                    'subcategorias': [
                        {
                            'nombre': s.nombre,
                            'url': s.get_absolute_url(),
                        } for s in c.subcategorias.all()
                    ],
                } for c in categorias
            ]
            cache.set(CAT_CACHE_KEY, categorias_data, 60 * 60 * 12)

        request.categorias_data = categorias_data

        return view_func(request, *args, **kwargs)
    return wrapper

def ordenby(request, productos):
    orden = request.GET.get('ordenby', '')
    if orden == 'price_lower':
        productos = productos.order_by('precio_orden')
        filtro = 'Menor precio'
    elif orden == 'price_higher':
        productos = productos.order_by('-precio_orden')
        filtro = 'Mayor precio'
    elif orden == 'date':
        productos = productos.order_by('-id')
        filtro = 'Los últimos'
    else:
        filtro = 'Ordenar por'
    return productos, filtro

def filtrar_atributo(params, productos, atributos_unicos):
    """
    Filtra productos según los atributos seleccionados en el querystring (request.GET).
    """
    for nombre_atributo, valores in params.lists():
        if nombre_atributo in atributos_unicos:
            productos = productos.filter(
                atributos__nombre=nombre_atributo,
                atributos__valor__in=valores
            )

    return productos.distinct()

def get_atributos_contados(productos):
    qs = (
        Atributo.objects
        .filter(producto__in=productos)
        .values('nombre', 'valor')
        .annotate(total=Count('producto', distinct=True))
    )
    resultado = defaultdict(list)
    for a in qs:
        resultado[a['nombre']].append({'valor': a['valor'], 'total': a['total']})
    return resultado

def filters(request,productos):
    atributos_previos = get_atributos_contados(productos)
    productos = filtrar_atributo(request.GET, productos, {k: [v['valor'] for v in vals] for k, vals in atributos_previos.items()})
    atributos_unicos = get_atributos_contados(productos)

    return productos,dict(atributos_unicos)

def cuotas_mp(precio) -> dict:
    """
    Calcula las cuotas de Mercado Pago para un precio dado.
    """
    coeficientes = {
        1 : 1.0,
        2 : 1.18339,
        3 : 1.2129,
        6 : 1.34239,
        9 : 1.4985,
        12 : 1.64499,
        18 : 2.05,
        24 : 2.46494
    }
    resultados = {}
    total_mp = round(precio*settings.MERCADOPAGO_COMMISSION,2)
    for cuota, coeficiente in coeficientes.items():
        total = round(total_mp*coeficiente,2)
        valor_couta = round(total/cuota,2)
        resultados[cuota] = {
            "valor_cuota":formato_pesos(valor_couta),
            "total":formato_pesos(total)
        }
    return resultados

def grid_meta_data(request:HttpRequest, productos:QuerySet[Producto], title:str,categoria_obj:Categoria=None,subcategoria_obj:SubCategoria=None) -> dict:
    """
    Genera un diccionario con metadatos para una página.
    """
    if productos.exists():
        prods = list(productos)
        count = len(prods)

        if categoria_obj and categoria_obj.descripcion_seo:
            description= f"{title} | {count} Resultados | {categoria_obj.descripcion_seo}"
        elif subcategoria_obj and subcategoria_obj.descripcion_seo:
            description= f"{title} | {count} Resultados | {subcategoria_obj.descripcion_seo}"
        else:
            description=f"{title} - Encontrá {count} producto/s en Twinstore. Ofertas y los mejores precios en tecnología."


        meta = {
            "title": f"{title} | Twinstore",
            "description": description,
            "url": request.build_absolute_uri(),
            "image": f"{request.build_absolute_uri('/static/img/mail.webp')}",
            "robots": "index, follow",
            "count": productos.count(),
        }
    else:
        meta = {
            "title": "Twinstore - Productos",
            "description": "No se encontraron productos disponibles. Visitá Twinstore para ver nuestro catálogo completo.",
            "url": request.build_absolute_uri(),
            "image": f"{request.build_absolute_uri('/static/img/mail.webp')}",
            "robots": "noindex, follow",
            "count": 0,
        }
    return meta

def prod_meta_data(request: HttpRequest, producto: Producto) -> dict:
    imagenes = list(producto.imagenes_producto.all()[:1])
    imagen = imagenes[0].imagen_200.url if imagenes else f"{request.build_absolute_uri('/static/img/mail.webp')}"

    meta = {
        "title": f"{producto.nombre} | Twinstore",
        "description": producto.descripcion_seo or f"Comprá {producto.nombre} en Twinstore. Ofertas y los mejores precios en tecnología.",
        "url": request.build_absolute_uri(producto.get_absolute_url()),
        "image": imagen,
        "robots": "index, follow",
        "price": float(producto.precio_final),
        "currency": "ARS",
        "og": {
            "type": "product",
            "title": f"{producto.nombre} | Twinstore",
            "description": producto.descripcion_seo or f"Comprá {producto.nombre} en Twinstore. Ofertas y precios actualizados.",
            "url": request.build_absolute_uri(producto.get_absolute_url()),
            "image": imagen,
            "site_name": "Twinstore",
        },
        "twitter": {
            "card": "summary_large_image",
            "title": f"{producto.nombre} | Twinstore",
            "description": producto.descripcion_seo or f"Encontrá {producto.nombre} al mejor precio en Twinstore.",
            "image": imagen,
        },
        "schema": json.dumps({
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": producto.nombre,
            "image": [imagen],
            "description": producto.descripcion_seo or f"Comprá {producto.nombre} en Twinstore.",
            "sku": producto.id,
            "offers": {
                "@type": "Offer",
                "url": request.build_absolute_uri(producto.get_absolute_url()),
                "priceCurrency": "ARS",
                "price": float(producto.precio_final),
                "availability": "https://schema.org/InStock" if producto.obtener_stock() > 0 else "https://schema.org/OutOfStock",
                "seller": {"@type": "Organization", "name": "Twinstore"}
            }
        }, ensure_ascii=False)
    }
    return meta