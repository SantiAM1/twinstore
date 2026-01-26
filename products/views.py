from django.http import Http404, JsonResponse,HttpRequest
from django.shortcuts import render

from .models import Producto, Categoria
from .utils import inject_categorias_subcategorias,cuotas_mp,grid_meta_data,prod_meta_data
from .types import GridContext
from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.db import models
from django.db.models import Count

from core.models import EventosPromociones
from django.utils import timezone

# Create your views here.
# ----- Prod View ----- #
def slug_dispatcher(request, slug):
    """
    Redirige a la vista correspondiente según el slug proporcionado.
    Categoria o Producto.
    """
    if Producto.objects.filter(slug=slug).exists():
        return producto_view(request, slug)
    if Categoria.objects.filter(slug=slug).exists():
        return categoria_view(request, slug)
    raise Http404("No se encontró el recurso solicitado.")

def producto_view(request: HttpRequest, slug: str):
    """
    Vista personal del producto.
    """
    producto = Producto.objects.vista_prefetch().get(slug=slug)

    mercado_pago_cuotas = cuotas_mp(float(producto.precio_final))

    imagenes_dict = producto.obtener_imagenes()

    reseñas = producto.reseñas.all()
    promedio = round(reseñas.aggregate(models.Avg('calificacion'))['calificacion__avg'] or 0,2)
    total = reseñas.count()

    stats = reseñas.values('calificacion').annotate(total=Count('id'))
    distribucion = {i: 0 for i in range(1, 6)}
    for s in stats:
        distribucion[s['calificacion']] = s['total']

    reviews = reseñas[:5]

    porcentajes = {
        k: int((v / total) * 100) if total > 0 else 0
        for k, v in sorted(distribucion.items(), reverse=True)
    }

    meta = prod_meta_data(request, producto)

    return render(request, 'products/producto_view.html', {
        'producto': producto,
        'imagenes_dict': imagenes_dict,
        'mercado_pago_cuotas': mercado_pago_cuotas,
        'reviews':{
            'total':total,
            'promedio':promedio,
            'usuarios':reviews
        },
        'porcentajes':porcentajes,
        'meta':meta
    })

# ----- ProdGrid ----- #
def products_grid_response(
        request: HttpRequest,
        ctx: GridContext,
        type_request: str = 'render'
        ):
    
    productos = ctx['productos']

    if type_request == 'json':
        mutable_get = request.GET.copy()
        mutable_get.pop('type', None)
        request.GET = mutable_get
        
        filters_nav = render_to_string('partials/filters-nav.html',{"title":"pass","marcas":ctx['marcas'],'atributos':ctx['atributos']},request=request)
        prod_grid = render_to_string('partials/prod-grid.html',{'productos':productos})
        filters_active = render_to_string('partials/active-filters.html',request=request)
        order_links = render_to_string('partials/order-links.html',request=request)
        return JsonResponse({'filtersNav':filters_nav,'prodGrid':prod_grid,'filtro':ctx['filtro'],'activeFilters':filters_active,'orderLinks':order_links,'title':ctx['title']})
    
    elif type_request == 'render':
        meta = grid_meta_data(
            request,
            productos,
            ctx["title"],
            categoria_obj=ctx.get('categoria', None),
            subcategoria_obj=ctx.get('sub_categoria_obj', None)
        )
        return render(request,'products/prod-grid.html',{
            **ctx,
            'categorias_data': request.categorias_data,
            'meta':meta
        })

@inject_categorias_subcategorias
def categoria_view(request:HttpRequest,slug:str):
    type_request = request.GET.get('type', 'render')

    ctx = Producto.objects.master_request(
        categoria_slug=slug,
        request=request,
        flag_filters=True
    )

    return products_grid_response(request, ctx, type_request)

@inject_categorias_subcategorias
def subcategoria_view(request:HttpRequest,categoria,subcategoria):
    type_request = request.GET.get('type', 'render')
    
    ctx = Producto.objects.master_request(
        subcategoria_slug=subcategoria,
        request=request,
        flag_filters=True
    )

    return products_grid_response(request, ctx, type_request)

@inject_categorias_subcategorias
def productos(request: HttpRequest):
    type_request = request.GET.get("type", "render")

    marca_slug = request.GET.get("marca")
    evento_slug = request.GET.get("evento")

    evento_obj = None
    if evento_slug:
        ahora = timezone.now()
        evento_obj = EventosPromociones.objects.filter(
            activo=True,
            fecha_inicio__lte=ahora,
            fecha_fin__gte=ahora,
            slug=evento_slug
        ).first()

    ctx = Producto.objects.master_request(
        marca_slug=marca_slug,
        evento=evento_obj,
        request=request
    )
    return products_grid_response(request, ctx, type_request)

# ----- Busqueda de productos ----- #
@inject_categorias_subcategorias
def busqueda_view(request:HttpRequest):
    q = request.GET.get('q','').strip().lower()
    type_request = request.GET.get('type', 'render')

    if not q or len(q) < 2:
        return redirect('products:grid')
    
    ctx = Producto.objects.master_request(
        busqueda=q,
        request=request,
        flag_filters=True
    )

    return products_grid_response(request, ctx, type_request)