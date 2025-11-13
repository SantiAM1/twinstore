from django.http import Http404, JsonResponse,HttpRequest
from django.shortcuts import render

from .models import Producto, SubCategoria,Marca,ImagenProducto,Categoria,ColorProducto
from .utils import inject_categorias_subcategorias,filters,ordenby,cuotas_mp,grid_meta_data,prod_meta_data
from django.db.models import Q
from django.template.loader import render_to_string
from .forms import EditarProducto
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import models
from django.db.models import Count

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
        .prefetch_related('colores__imagenes_color', 'imagenes_producto','especificaciones','reseñas','reseñas__usuario')
        .get(slug=slug)
    )

    mercado_pago_cuotas = cuotas_mp(float(producto.precio))

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
def productos_filters(request:HttpRequest,type:str='render',subcategoria_slug:str=None,categoria_slug:str=None,flag_filters:bool=False,marca_request:str=None,busqueda:str=None):
    """
    Filtra los productos según los parámetros proporcionados.
    Si no hay parametros, devuelve todos los productos.
    1. subcategoria_slug: Filtra por subcategoría si se proporciona.
    2. categoria_slug: Filtra por categoría si se proporciona.
    3. marca: Filtra por marca si se proporciona.
    4. busqueda: Filtra por término de búsqueda si se proporciona.
    5. flag_filters: Si es True, aplica filtros adicionales.
    6. type: Define el tipo de respuesta ('json' o django 'render').
    """
    if subcategoria_slug:
        subcategoria = get_object_or_404(SubCategoria,slug=subcategoria_slug)
        productos = Producto.objects.filter(sub_categoria=subcategoria).prefetch_related("colores__imagenes_color","imagenes_producto")
        title = subcategoria.nombre
    
    elif categoria_slug:
        categoria = get_object_or_404(Categoria, slug=categoria_slug)
        sub_categorias = (
            SubCategoria.objects
            .filter(categoria=categoria)
            .annotate(total=Count('productos', distinct=True))
        )
        productos = Producto.objects.filter(sub_categoria__in=sub_categorias).prefetch_related("colores__imagenes_color","imagenes_producto")
        title = categoria.nombre

    else:
        if marca_request:
            marca = Marca.objects.get(slug=marca_request)
            productos = Producto.objects.filter(marca=marca).prefetch_related("colores__imagenes_color","imagenes_producto")
            title = marca.nombre
        elif busqueda:
            productos = (
                Producto.objects
                .filter(
                    Q(nombre__icontains=busqueda) | Q(slug__icontains=busqueda)
                )
                .prefetch_related("colores__imagenes_color", "imagenes_producto")
            )
            title = f'Resultados de busqueda'
        else:
            productos = Producto.objects.all().prefetch_related("colores__imagenes_color","imagenes_producto")
            title = 'Productos'

    if flag_filters:
        marca_seleccionada = request.GET.get('Marca')
        if marca_seleccionada:
            productos = productos.filter(marca__nombre=marca_seleccionada)
        productos,atributos_unicos = filters(request,productos)
        marcas = (
            Marca.objects
            .filter(producto__in=productos)
            .annotate(total=Count('producto', distinct=True))
            .distinct()
        )
    else:
        marcas = {}
        atributos_unicos = {}

    productos, filtro=ordenby(request,productos)

    if type == 'json':
        mutable_get = request.GET.copy()
        mutable_get.pop('type', None)
        request.GET = mutable_get
        
        filters_nav = render_to_string('partials/filters-nav.html',{"title":"pass","marcas":marcas,'atributos':atributos_unicos},request=request)
        prod_grid = render_to_string('partials/prod-grid.html',{'productos':productos})
        filters_active = render_to_string('partials/active-filters.html',request=request)
        order_links = render_to_string('partials/order-links.html',request=request)
        return JsonResponse({'filtersNav':filters_nav,'prodGrid':prod_grid,'filtro':filtro,'activeFilters':filters_active,'orderLinks':order_links,'title':title})

    elif type == 'render':
        meta = grid_meta_data(
            request,
            productos,
            title,
            categoria_obj=categoria if categoria_slug else None,
            subcategoria_obj=subcategoria if subcategoria_slug else None
            )
        return render(request,'products/prod-grid.html',{
            'productos': productos,
            'categorias_data': request.categorias_data,
            'marcas':marcas,
            'title':title,
            'filtro':filtro,
            'atributos':atributos_unicos,
            'sub_categorias': sub_categorias if categoria_slug else None,
            'meta':meta
        })
    
    return Http404("Type no válido")

@inject_categorias_subcategorias
def categoria_view(request:HttpRequest,slug:str):
    type_request = request.GET.get('type', 'render')
    return productos_filters(request,type_request,categoria_slug=slug,flag_filters=True)

@inject_categorias_subcategorias
def subcategoria_view(request:HttpRequest,categoria,subcategoria):
    type_request = request.GET.get('type', 'render')
    return productos_filters(request,type_request,subcategoria_slug=subcategoria,flag_filters=True)

@inject_categorias_subcategorias
def productos(request:HttpRequest):
    type_request = request.GET.get('type', 'render')
    marca_request = request.GET.get('Marca', None)
    return productos_filters(request,type_request,marca_request=marca_request)

# ----- Busqueda de productos ----- #
@inject_categorias_subcategorias
def busqueda_view(request:HttpRequest):
    q = request.GET.get('q','').strip().lower()
    type_request = request.GET.get('type', 'render')

    if not q or len(q) < 2:
        return redirect('products:grid')
    
    return productos_filters(request,type_request,flag_filters=True,busqueda=q)
