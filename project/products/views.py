from django.http import Http404, JsonResponse
from django.shortcuts import render

from core.decorators import bloquear_si_mantenimiento
from .models import Producto, SubCategoria,Marca,ImagenProducto,Categoria
from django.db.models import Q
from django_user_agents.utils import get_user_agent
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from .forms import EditarProducto,ImagenProductoForm
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from rest_framework.decorators import throttle_classes
from core.throttling import FiltrosDinamicosThrottle

import json

# Create your views here.
# ----- Manejo de filtros ----- #
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

def return_filtros_dinamicos(request, categoria_obj,subcategoria_obj=None,type='default'):
    sub_categorias = SubCategoria.objects.filter(categoria=categoria_obj)
    productos = Producto.objects.filter(sub_categoria__in=sub_categorias).select_related('marca', 'sub_categoria').prefetch_related('atributos')

    if subcategoria_obj:
        productos = productos.filter(sub_categoria=subcategoria_obj)

    #* 🔹 Filtrar por marcas
    marca_seleccionada = request.GET.get('marca')
    if marca_seleccionada:
        productos = productos.filter(marca__nombre=marca_seleccionada)

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

    prod_totales = len(productos)
    
    pagina_actual = request.GET.get('pagina', 1)
    paginator = Paginator(productos, 12)
    pagina = paginator.get_page(pagina_actual)
    productos = pagina.object_list

    filtros_aplicados = {key: value for key, value in request.GET.items() if key not in ["ordenby", "q","pagina"]}

    if type == 'default':
        return productos, sub_categorias, atributos_unicos, marcas, pagina, filtros_aplicados, filtro,prod_totales,subcategoria_obj
    elif type == 'ajax':
        user_agent = get_user_agent(request)
        if user_agent.is_mobile:
            html_filtros = render_to_string(
                'partials/filtros_dinamicos_mobile.html',{
                    'atributos_unicos': atributos_unicos,
                    'request':request,
                    'sub_categorias':sub_categorias,
                    'subcategoria_obj':subcategoria_obj,
                    'marcas':marcas,
                    'categoria' :categoria_obj,
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
            html_paginacion = render_to_string('partials/paginacion.html', {
            'pagina':pagina},
            request=request
            )
            return JsonResponse({'activos':html_activos,'html':html,'filtros':html_filtros,'paginacion':html_paginacion})

        html_filtros = render_to_string(
            'partials/filtros_dinamicos.html', {
                'filtros_aplicados':filtros_aplicados,
                'request': request,
                'sub_categorias': sub_categorias,
                'atributos_unicos': atributos_unicos,
                'marcas': marcas,
                'subcategoria_obj':subcategoria_obj,
                'categoria':categoria_obj
            },
            request=request
        )
        html_navlinks = render_to_string('partials/header_links.html',{
            'categoria':categoria_obj,
            'sub_categorias':sub_categorias,
            'subcategoria_obj':subcategoria_obj
        },request=request)
        html_orden = render_to_string('partials/orden_resultado.html',{
            'filtro':filtro,
            'pagina':pagina
        },request=request)
        html = render_to_string('partials/product_grid.html', {
            'productos': productos
        }, request=request)
        html_paginacion = render_to_string('partials/paginacion.html', {
            'pagina':pagina},
            request=request
            )
        return JsonResponse({'html': html,'filtros':html_filtros,'navlinks':html_navlinks,'orden':html_orden,'paginacion':html_paginacion})

# ----- Categoria AJAX ----- #
@bloquear_si_mantenimiento
@throttle_classes([FiltrosDinamicosThrottle])
def categoria_ajax(request, categoria):
    categoria_obj = get_object_or_404(Categoria, slug=categoria)
    return return_filtros_dinamicos(request, categoria_obj,type='ajax')

# ----- Filtracion por categoria ----- #
def categoria(request, categoria):
    categoria_obj = get_object_or_404(Categoria, slug=categoria)
    productos, sub_categorias, atributos_unicos, marcas, pagina, filtros_aplicados, filtro,prod_totales,subcategoria_obj = return_filtros_dinamicos(request, categoria_obj,type='default')

    template = 'products/mobile.html' if get_user_agent(request).is_mobile else 'products/category.html'

    return render(request, template,{
        'productos': productos,
        'categoria': categoria_obj,
        'sub_categorias':sub_categorias,
        'filtro' : filtro,
        'atributos_unicos':atributos_unicos,
        'marcas':marcas,
        'filtros_aplicados':filtros_aplicados,
        'pagina':pagina,
    })

# ----- Filtracion por categoria y subcategoria ----- #
@bloquear_si_mantenimiento
@throttle_classes([FiltrosDinamicosThrottle])
def subcategoria_ajax(request, categoria, subcategoria):
    categoria_obj = get_object_or_404(Categoria, slug=categoria)
    subcategoria_obj = get_object_or_404(SubCategoria, slug=subcategoria, categoria=categoria_obj)
    return return_filtros_dinamicos(request, categoria_obj, subcategoria_obj,type='ajax')

def categoria_subcategoria(request, categoria, subcategoria):
    categoria_obj = get_object_or_404(Categoria, slug=categoria)
    subcategoria_obj = get_object_or_404(SubCategoria, slug=subcategoria, categoria=categoria_obj)

    productos, sub_categorias, atributos_unicos, marcas, pagina, filtros_aplicados, filtro,prod_totales,subcategoria_obj = return_filtros_dinamicos(
        request, categoria_obj, subcategoria_obj,type='default'
    )

    template = 'products/mobile.html' if get_user_agent(request).is_mobile else 'products/category.html'

    return render(request, template, {
        'productos': productos,
        'categoria': categoria_obj,
        'sub_categorias': sub_categorias,
        'filtro': filtro,
        'atributos_unicos': atributos_unicos,
        'marcas': marcas,
        'filtros_aplicados': filtros_aplicados,
        'pagina': pagina,
        'subcategoria_obj': subcategoria_obj,
    })

# ----- Busqueda de productos ----- #
def return_busqueda(request,type='default'):
    query = request.GET.get('q', '')
    pagina_actual = request.GET.get('pagina', 1)

    if query:
        palabras = query.split()
        productos = Producto.objects.filter(
            Q(nombre__icontains=palabras[0])
        )
        for palabra in palabras[1:]:
            productos = productos.filter(Q(nombre__icontains=palabra))
    else:
        productos =Producto.objects.all()
    
    productos, filtro = ordenby(request, productos)
    paginator = Paginator(productos, 12)
    pagina = paginator.get_page(pagina_actual)
    productos = pagina.object_list

    if type == 'default':
        return render(request, 'products/search_filter.html', {
            'productos': productos,
            'query': query,
            'filtro': filtro,
            'pagina':pagina
        })
    elif type == 'ajax':
        html_productos = render_to_string('partials/product_grid.html',{'productos':productos})
        html_pagina = render_to_string('partials/paginacion.html',{'pagina':pagina})
        html_filtro = render_to_string('partials/orden_resultado.html',{'filtro':filtro,'pagina':pagina})
        return JsonResponse({'html':html_productos,'paginacion':html_pagina,'orden':html_filtro})

@bloquear_si_mantenimiento
@throttle_classes([FiltrosDinamicosThrottle])
def buscar_productos_ajax(request):
    return return_busqueda(request,type='ajax')

def buscar_productos(request):
    return return_busqueda(request,type='default')

def return_gaming(request,type='default'):
    productos = Producto.objects.filter(etiquetas__nombre="gaming")
    pagina_actual = request.GET.get('pagina', 1)

    productos, filtro = ordenby(request, productos)
    paginator = Paginator(productos, 12)
    pagina = paginator.get_page(pagina_actual)
    productos = pagina.object_list

    if type == 'default':
        return render(request, 'products/gaming.html', {
            'productos': productos,
            'filtro': filtro,
            'pagina':pagina
        })
    elif type == 'ajax':
        html_productos = render_to_string('partials/product_grid.html',{'productos':productos})
        html_pagina = render_to_string('partials/paginacion.html',{'pagina':pagina})
        html_filtro = render_to_string('partials/orden_resultado.html',{'filtro':filtro,'pagina':pagina})
        return JsonResponse({'html':html_productos,'paginacion':html_pagina,'orden':html_filtro})

@bloquear_si_mantenimiento
@throttle_classes([FiltrosDinamicosThrottle])
def gaming_ajax(request):
    return return_gaming(request,"ajax")

def gaming(request):
    return return_gaming(request,"default")

# ----- Vista individual del producto ----- #
def producto_view(request,product_slug):
    producto = Producto.objects.get(slug=product_slug)
    imagenes = producto.imagenes.all()
    thumbnails = [img.imagen_100.url for img in imagenes]
    thumbnails_json = json.dumps(thumbnails)
    return render(request,'products/producto_view.html',{
        'producto':producto,
        'imagenes':imagenes,
        'thumbnails':thumbnails_json
        })

def slug_dispatcher(request, slug):
    producto = Producto.objects.filter(slug=slug).first()
    if producto:
        return producto_view(request, slug)

    cat = Categoria.objects.filter(slug=slug).first()
    if cat:
        return categoria(request, cat.slug)

    # No encontrado
    raise Http404("No se encontró ningún recurso con ese slug.")


# * Solo admin o staff
@staff_member_required
def editar_producto_view(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        form = EditarProducto(request.POST, request.FILES, instance=producto)

        if form.is_valid():
            form.save()
            messages.success(request, 'Producto editado correctamente.')
            return redirect('products:editar_producto', pk=producto.pk)
    else:
        form = EditarProducto(instance=producto)
        imagenes = producto.imagenes.all()
        cantidad_actual = imagenes.count()
        cantidad_maxima = 4
        cantidad_restante = cantidad_maxima - cantidad_actual

        formularios_nuevos = [ImagenProductoForm() for _ in range(cantidad_restante)]

    return render(request, 'products/editar_producto.html',{
        'form': form,
        'producto': producto,
        'formularios_nuevos': formularios_nuevos,
        'imagenes': imagenes,
        })

# * Solo admin o staff
@staff_member_required
def agregar_imagenes(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        for archivo in request.FILES.getlist('imagen'):
            if archivo:
                ImagenProducto.objects.create(
                    producto=producto,
                    imagen=archivo
                )
        messages.success(request, 'Imagen/es cargada/s correctamente.')
        return redirect('products:editar_producto', pk=producto.pk)

# * Solo admin o staff
@staff_member_required
def eliminar_imagen(request, img_id):
    imagen = get_object_or_404(ImagenProducto, id=img_id)
    producto_id = imagen.producto.id

    imagen.delete()
    messages.success(request, 'Imagen eliminada correctamente.')
    return redirect('products:editar_producto', pk=producto_id)