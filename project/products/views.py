from django.http import JsonResponse
from django.shortcuts import render
from .models import Producto, SubCategoria,Marca,ImagenProducto
from django.db.models import Q
from django_user_agents.utils import get_user_agent
from django.template.loader import render_to_string
import time
from django.db.models import F, FloatField, ExpressionWrapper
from django.core.paginator import Paginator
from .forms import EditarProducto,ImagenProductoForm
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
import os
# Create your views here.
# ----- Manejo de filtros ----- #
def get_atributos(productos):
    atributos_unicos = {}
    for producto in productos:
        for atributo in producto.atributos.all():
            if atributo.nombre not in atributos_unicos:
                atributos_unicos[atributo.nombre] = set()
            atributos_unicos[atributo.nombre].add(atributo.valor)

    atributos_unicos = {k: list(v) for k, v in atributos_unicos.items()}
    return atributos_unicos

def filtrar_atributo(dict, productos, atributos_unicos):
    filtros = {}

    for nombre_atributo, valores in dict.lists():  # permite múltiples valores por clave
        if nombre_atributo in atributos_unicos:
            filtros[nombre_atributo] = valores

    # Aplicamos los filtros individualmente (AND lógico)
    for atributo, valores in filtros.items():
        productos = productos.filter(
            atributos__nombre=atributo,
            atributos__valor__in=valores
        )
    
    return productos.distinct()

# ----- Busqueda de productos ----- #
def buscar_productos(request):
    query = request.GET.get('q', '')

    #* Si encuentra una busqueda procede a realizar el filtro
    if query:
        palabras = query.split()
        productos = Producto.objects.filter(
            Q(nombre__icontains=palabras[0])
        )
        for palabra in palabras[1:]:
            productos = productos.filter(Q(nombre__icontains=palabra))

        productos, filtro = ordenby(request, productos)

        pagina_actual = request.GET.get('pagina', 1)
        paginator = Paginator(productos, 12)
        pagina = paginator.get_page(pagina_actual)

        productos = pagina.object_list

        return render(request, 'products/search_filter.html', {
            'productos_imagen': productos,
            'cantidad_productos': len(productos),
            'query': query,
            'filtro': filtro,
            'pagina':pagina
        })

    #* En el caso de no encontrar nada se muestran todos los productos
    productos =Producto.objects.all()
    productos, filtro = ordenby(request, productos)

    pagina_actual = request.GET.get('pagina', 1)
    paginator = Paginator(productos, 12)
    pagina = paginator.get_page(pagina_actual)

    productos = pagina.object_list

    return render(request, 'products/search_filter.html', {
            'productos': productos,
            'cantidad_productos': len(productos),
            'query': query,
            'filtro': filtro,
            'pagina':pagina
        })

# ----- Categoria AJAX ----- #
def categoria_ajax(request, categoria):
    sub_categorias = SubCategoria.objects.filter(categoria__nombre=categoria)

    productos = Producto.objects.filter(sub_categoria__in=sub_categorias).select_related('marca', 'sub_categoria').prefetch_related('imagenes', 'atributos')

    #* 🔹 Filtrar por marcas
    marca_seleccionada = request.GET.get('marca')
    if marca_seleccionada:
        productos = productos.filter(marca__nombre=marca_seleccionada)

    #* 🔹 Filtrar por subcategorias
    sub_categoria_seleccionada = request.GET.get('sub_categoria')
    if sub_categoria_seleccionada:
        productos = productos.filter(sub_categoria__nombre=sub_categoria_seleccionada)

    #* 🔹 Obtener atributos antes del filtro
    atributos_previos = get_atributos(productos)

    #* 🔹 Aplicar filtros
    productos = filtrar_atributo(request.GET, productos, atributos_previos)

    #* 🔹 Obtener solo los atributos válidos después del filtro
    atributos_unicos = get_atributos(productos)

    marcas = Marca.objects.filter(producto__in=productos).distinct()

    sub_categorias = SubCategoria.objects.filter(productos__in=productos).distinct()

    #* 🔹 Ordenar los productos
    productos, filtro=ordenby(request,productos)

    pagina_actual = request.GET.get('pagina', 1)
    paginator = Paginator(productos, 12)
    pagina = paginator.get_page(pagina_actual)
    productos = pagina.object_list

    filtros_aplicados = {key: value for key, value in request.GET.items() if key not in ["ordenby", "q","pagina"]}
    print(filtros_aplicados)
    user_agent = get_user_agent(request)
    if user_agent.is_mobile:

        html_filtros = render_to_string(
            'partials/filtros_dinamicos_mobile.html',{
                'atributos_unicos': atributos_unicos,
                'request':request,
                'sub_categorias':sub_categorias,
                'marcas':marcas
            }, request=request
            )

        html = render_to_string('partials/product_grid.html', {
            'productos': productos,
            'pagina':pagina
        }, request=request)

        html_activos = render_to_string(
        'partials/filtros_activos_mobile.html', {
            'filtros_aplicados':filtros_aplicados,
            'request': request,
        },
        request=request
        )

        return JsonResponse({'activos':html_activos,'html':html,'filtros':html_filtros})

    html_filtros = render_to_string(
        'partials/filtros_dinamicos.html', {
            'filtros_aplicados':filtros_aplicados,
            'request': request,
            'sub_categorias': sub_categorias,
            'atributos_unicos': atributos_unicos,
            'marcas': marcas,
        },
        request=request
    )

    html_navlinks = render_to_string('partials/header_links.html',{
        'categoria':categoria,
        'sub_categorias':sub_categorias
    },request=request)

    html_orden = render_to_string('partials/orden_resultado.html',{
        'cantidad_productos':len(productos),
        'filtro':filtro,
        'request':request
    },request=request)

    html = render_to_string('partials/product_grid.html', {
        'productos': productos
    }, request=request)

    html_paginacion = render_to_string('partials/paginacion.html', {
        'pagina':pagina},
        request=request
        )

    return JsonResponse({'html': html,'filtros':html_filtros,'navlinks':html_navlinks,'orden':html_orden,'paginacion':html_paginacion})

# ----- Filtracion por categoria ----- #
def categoria(request, categoria):
    print('categoria_sin_ajax')
    sub_categorias = SubCategoria.objects.filter(categoria__nombre=categoria)
    productos = Producto.objects.filter(sub_categoria__in=sub_categorias).select_related('marca', 'sub_categoria').prefetch_related('imagenes', 'atributos')

    #* 🔹 Filtrar por marcas
    marca_seleccionada = request.GET.get('marca')
    if marca_seleccionada:
        productos = productos.filter(marca__nombre=marca_seleccionada)

    #* 🔹 Filtrar por subcategorias
    sub_categoria_seleccionada = request.GET.get('sub_categoria')
    if sub_categoria_seleccionada:
        productos = productos.filter(sub_categoria__nombre=sub_categoria_seleccionada)

    #* 🔹 Obtener atributos antes del filtro
    atributos_previos = get_atributos(productos)

    #* 🔹 Aplicar filtros
    productos = filtrar_atributo(request.GET, productos, atributos_previos)

    #* 🔹 Obtener solo los atributos válidos después del filtro
    atributos_unicos = get_atributos(productos)

    marcas = Marca.objects.filter(producto__in=productos).distinct()
    sub_categorias = SubCategoria.objects.filter(productos__in=productos).distinct()

    #* 🔹 Ordenar los productos
    productos, filtro=ordenby(request,productos)
    
    pagina_actual = request.GET.get('pagina', 1)
    paginator = Paginator(productos, 12)
    pagina = paginator.get_page(pagina_actual)
    productos = pagina.object_list

    filtros_aplicados = {key: value for key, value in request.GET.items() if key not in ["ordenby", "q","pagina"]}

    user_agent = get_user_agent(request)
    if user_agent.is_mobile:
        return render(request,'products/mobile.html',{
        'productos': productos,
        'categoria': categoria,
        'sub_categorias':sub_categorias,
        'cantidad_productos':len(productos),
        'filtro' : filtro,
        'atributos_unicos':atributos_unicos,
        'marcas':marcas,
        'filtros_aplicados':filtros_aplicados
    })

    return render(request, 'products/category.html', {
        'productos': productos,
        'categoria': categoria,
        'sub_categorias':sub_categorias,
        'cantidad_productos':len(productos),
        'filtro' : filtro,
        'atributos_unicos':atributos_unicos,
        'marcas':marcas,
        'filtros_aplicados':filtros_aplicados,
        'pagina':pagina
    })

# ----- Ordenar los productos ----- #
def ordenby(request, productos):
    orden = request.GET.get('ordenby', 'date')
    if orden == 'price_lower':
        productos = productos.order_by('precio')
        filtro = 'Ordenar por precio: menor a mayor'
    elif orden == 'price_higher':
        productos = productos.order_by('-precio')
        filtro = 'Ordenar por precio: mayor a menor'
    else:
        productos = productos.order_by('-id')
        filtro = 'Ordenar por los últimos'

    return productos, filtro

# ----- Vista individual del producto ----- #
def producto_view(request,product_name):
    producto = Producto.objects.get(nombre=product_name)
    imagenes = producto.imagenes.all()
    return render(request,'products/producto_view.html',{
        'producto':producto,
        'imagenes':imagenes
        })

# * Solo admin o staff
@user_passes_test(lambda u: u.is_staff)
def editar_producto_view(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        form = EditarProducto(request.POST, request.FILES, instance=producto)

        if form.is_valid():
            form.save()

            return redirect('products:editar_producto', pk=producto.pk)
    else:
        form = EditarProducto(instance=producto)
        imagenes = producto.imagenes.all()
        cantidad_actual = imagenes.count()
        cantidad_maxima = 5
        cantidad_restante = cantidad_maxima - cantidad_actual

        formularios_nuevos = [ImagenProductoForm() for _ in range(cantidad_restante)]

    return render(request, 'products/editar_producto.html',{
        'form': form,
        'producto': producto,
        'formularios_nuevos': formularios_nuevos,
        'imagenes': imagenes,
        })

# * Solo admin o staff
@user_passes_test(lambda u: u.is_staff)
def agregar_imagenes(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        for key in request.FILES:
            archivo = request.FILES[key]
            if archivo:
                ImagenProducto.objects.create(
                    producto=producto,
                    imagen=archivo
                )
        return redirect('products:editar_producto', pk=producto.pk)

# * Solo admin o staff
@user_passes_test(lambda u: u.is_staff)
def eliminar_imagen(request, img_id):
    imagen = get_object_or_404(ImagenProducto, id=img_id)
    producto_id = imagen.producto.id

    if imagen.imagen and os.path.isfile(imagen.imagen.path):
        os.remove(imagen.imagen.path)

    imagen.delete()
    return redirect('products:editar_producto', pk=producto_id)