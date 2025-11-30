from django.http import Http404, JsonResponse,HttpRequest
from django.shortcuts import render

from .models import Producto, SubCategoria,Marca,ImagenProducto,Categoria,ColorProducto
from .utils import inject_categorias_subcategorias,filters,ordenby,cuotas_mp,grid_meta_data,prod_meta_data
from .types import GridContext
from django.db.models import Q
from django.template.loader import render_to_string
from .forms import EditarProducto
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import models
from django.db.models import Count,Prefetch

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
    producto = (
        Producto.objects
        .prefetch_related(
            'colores__imagenes_color',
            'imagenes_producto',
            'especificaciones',
            'reseñas',
            'reseñas__usuario')
            .get(slug=slug)
        )

    mercado_pago_cuotas = cuotas_mp(float(producto.precio_final))

    imagenes_dict = producto.obtener_imagenes()

    reseñas = producto.reseñas.all()
    promedio = round(reseñas.aggregate(models.Avg('calificacion'))['calificacion__avg'] or 0,2)
    total = reseñas.count()

    stats = reseñas.values('calificacion').annotate(total=Count('id'))
    distribucion = {i: 0 for i in range(1, 6)}
    for s in stats:
        distribucion[s['calificacion']] = s['total']

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
            'usuarios':reseñas
        },
        'porcentajes':porcentajes,
        'meta':meta
    })

# * Solo admin o staff
@staff_member_required
def editar_producto_view(request, pk):
    producto = Producto.objects.filter(pk=pk).prefetch_related('imagenes_producto','colores__imagenes_color').get(pk=pk)

    if request.method == 'POST':
        form = EditarProducto(request.POST, request.FILES, instance=producto)

        if form.is_valid():
            form.save()
            messages.success(request, 'Producto editado correctamente.')
            return redirect('products:editar_producto', pk=producto.pk)
    else:
        form = EditarProducto(instance=producto)

    return render(request, 'products/editar_producto.html',{
        'form': form,
        'producto': producto,
        })

@staff_member_required
def agregar_color(request,producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        nombres = request.POST.getlist('nombre_color[]')
        codigos = request.POST.getlist('codigo_color[]')

        for nombre, codigo in zip(nombres, codigos):
            if nombre and codigo:
                ColorProducto.objects.create(
                    producto=producto,
                    nombre=nombre.capitalize(),
                    hex=codigo
                )
                messages.success(request, 'Color/es agregado/s correctamente.')

    return redirect('products:editar_producto', pk=producto.pk)

@staff_member_required
def eliminar_color(request, color_id):
    color = get_object_or_404(ColorProducto, id=color_id)
    producto_id = color.producto.id

    color.delete()
    messages.success(request, 'Color eliminado correctamente.')
    return redirect('products:editar_producto', pk=producto_id)

@staff_member_required
def agregar_imagenes(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        for archivo in request.FILES.getlist('imagenes_producto[]'):
            if archivo:
                ImagenProducto.objects.create(
                    producto=producto,
                    imagen=archivo
                )
        messages.success(request, 'Imagen/es cargada/s correctamente.')

    return redirect('products:editar_producto', pk=producto.pk)

@staff_member_required
def asociar_color_img(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == 'POST':
        imagenes = request.POST.getlist('imagen_id')
        colores = request.POST.getlist('color_id')
        for imagen_id, color_id in zip(imagenes, colores):
            if imagen_id and color_id:
                imagen = get_object_or_404(ImagenProducto, id=imagen_id, producto=producto)
                color = get_object_or_404(ColorProducto, id=color_id, producto=producto)
                imagen.color = color
                imagen.save()
                messages.success(request, f'Color {color.nombre} asociado a la imagen correctamente.')
    
    return redirect('products:editar_producto', pk=producto.pk)

@staff_member_required
def eliminar_imagen(request, img_id):
    imagen = get_object_or_404(ImagenProducto, id=img_id)
    producto_id = imagen.producto.id

    imagen.delete()
    messages.success(request, 'Imagen eliminada correctamente.')
    return redirect('products:editar_producto', pk=producto_id)

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