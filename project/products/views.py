from django.http import JsonResponse
from django.shortcuts import render
from .models import Producto, SubCategoria,Marca
from django.db.models import Q
from django_user_agents.utils import get_user_agent
from django.template.loader import render_to_string

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

    # Recolectar los filtros seleccionados
    for nombre_atributo, valores in dict.items():
        if nombre_atributo in atributos_unicos:  # Asegurar que el filtro es válido
            filtros[nombre_atributo] = valores

    # Aplicar los filtros solo si existen
    if filtros:
        productos = productos.filter(
            atributos__nombre__in=filtros.keys(),
            atributos__valor__in=filtros.values()
        ).distinct()
    return productos

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
        productos_imagen = get_prod_img(productos)

        return render(request, 'products/search_filter.html', {
            'productos_imagen': productos_imagen,
            'cantidad_productos': len(productos),
            'query': query,
            'filtro': filtro
        })

    #* En el caso de no encontrar nada se muestran todos los productos
    productos =Producto.objects.all()
    productos, filtro = ordenby(request, productos)
    productos_imagen = get_prod_img(productos)
    return render(request, 'products/search_filter.html', {
            'productos_imagen': productos_imagen,
            'cantidad_productos': len(productos),
            'query': query,
            'filtro': filtro
        })

# ----- Categoria AJAX ----- #
def categoria_ajax(request, categoria):
    sub_categorias = SubCategoria.objects.filter(categoria__nombre=categoria)
    productos = Producto.objects.filter(sub_categoria__in=sub_categorias).prefetch_related('imagenes', 'atributos')
    marcas = Marca.objects.filter(producto__in=productos).distinct()

    #* 🔹 Filtrar por marcas
    marca_seleccionada = request.GET.get('marca')
    if marca_seleccionada:
        productos = productos.filter(marca__nombre=marca_seleccionada)

    #* 🔹 Filtrar por subcategorias
    sub_categoria_seleccionada = request.GET.get('sub_categoria')
    if sub_categoria_seleccionada:
        productos = productos.filter(sub_categoria__nombre=sub_categoria_seleccionada)

    #* 🔹 Obtener los atributos
    atributos_unicos = get_atributos(productos)

    #* 🔹 Filtrar productos segun los atributos
    productos = filtrar_atributo(request.GET,productos,atributos_unicos)

    #* 🔹 Ordenar los productos
    productos, filtro=ordenby(request,productos)

    #* 🔹 Obtener imágenes de los productos
    productos_imagen=get_prod_img(productos)

    filtros_aplicados = {key: value for key, value in request.GET.items() if key not in ["ordenby", "q"]}

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
            'productos_imagen': productos_imagen
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
        'productos_imagen': productos_imagen
    }, request=request)

    return JsonResponse({'html': html,'filtros':html_filtros,'navlinks':html_navlinks,'orden':html_orden})

# ----- Filtracion por categoria ----- #
def categoria(request, categoria):
    sub_categorias = SubCategoria.objects.filter(categoria__nombre=categoria)
    productos = Producto.objects.filter(sub_categoria__in=sub_categorias).prefetch_related('imagenes', 'atributos')
    marcas = Marca.objects.filter(producto__in=productos).distinct()

    #* 🔹 Filtrar por marcas
    marca_seleccionada = request.GET.get('marca')
    if marca_seleccionada:
        productos = productos.filter(marca__nombre=marca_seleccionada)

    #* 🔹 Filtrar por subcategorias
    sub_categoria_seleccionada = request.GET.get('sub_categoria')
    if sub_categoria_seleccionada:
        productos = productos.filter(sub_categoria__nombre=sub_categoria_seleccionada)

    #* 🔹 Obtener los atributos
    atributos_unicos = get_atributos(productos)

    #* 🔹 Filtrar productos segun los atributos
    productos = filtrar_atributo(request.GET,productos,atributos_unicos)

    #* 🔹 Ordenar los productos
    productos, filtro=ordenby(request,productos)

    #* 🔹 Obtener imágenes de los productos
    productos_imagen=get_prod_img(productos)

    filtros_aplicados = {key: value for key, value in request.GET.items() if key not in ["ordenby", "q"]}

    user_agent = get_user_agent(request)
    if user_agent.is_mobile:
        return render(request,'products/mobile.html',{
        'productos_imagen': productos_imagen,
        'categoria': categoria,
        'sub_categorias':sub_categorias,
        'cantidad_productos':len(productos),
        'filtro' : filtro,
        'atributos_unicos':atributos_unicos,
        'marcas':marcas,
        'filtros_aplicados':filtros_aplicados
    })

    return render(request, 'products/category.html', {
        'productos_imagen': productos_imagen,
        'categoria': categoria,
        'sub_categorias':sub_categorias,
        'cantidad_productos':len(productos),
        'filtro' : filtro,
        'atributos_unicos':atributos_unicos,
        'marcas':marcas,
        'filtros_aplicados':filtros_aplicados
    })

# ----- Vista individual del producto ----- #
def producto_view(request,product_name):
    producto = Producto.objects.get(nombre=product_name)
    imagenes = producto.imagenes.all()
    return render(request,'products/producto_view.html',{
        'producto':producto,
        'imagenes':imagenes
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

# ----- Obetener las imagenes de los productos ----- #
def get_prod_img(productos):
    productos_imagen = []
    for producto in productos:
        imagen_principal = producto.imagenes.first()
        if imagen_principal:
            imagen_url = imagen_principal.imagen.url
        else:
            imagen_url = None
        productos_imagen.append((producto, imagen_url))
    return productos_imagen