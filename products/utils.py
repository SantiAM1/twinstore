from functools import wraps
from django.core.cache import cache
from products.models import Categoria,Atributo,Producto,SubCategoria
from collections import defaultdict
from django.db.models import Count,QuerySet
from django.conf import settings
from payment.templatetags.custom_filters import formato_pesos
from django.http import HttpRequest
import json

def inject_categorias_subcategorias(view_func):
    """
    Decorador que envia a la vista las categorias y las subcategorias.
    Se utiliza en prodGrid.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        categorias_data = cache.get('categorias_con_subcategorias')
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
            cache.set('categorias_con_subcategorias', categorias_data, 60 * 60 * 12)

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