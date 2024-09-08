from ast import Sub
from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse,JsonResponse
from .models import Producto, SubCategoria,Categoria,Marca
from django.urls import reverse

# Create your views here.

def categoria(request, categoria):
    sub_categorias = SubCategoria.objects.filter(categoria__nombre=categoria)
    productos = Producto.objects.filter(sub_categoria__in=sub_categorias).prefetch_related('imagenes')

    # Capturar el valor del filtro de orden
    orden = request.GET.get('ordenby', 'date')  # Valor por defecto 'date'

    # Ordenar productos según el filtro seleccionado
    if orden == 'price_lower':
        productos = productos.order_by('precio')  # Orden ascendente
    elif orden == 'price_higher':
        productos = productos.order_by('-precio')  # Orden descendente
    else:
        productos = productos.order_by('-id')  # Orden por defecto, productos más recientes primero

    productos_imagen = []
    for producto in productos:
        imagen_principal = producto.imagenes.filter(imagen__endswith='_1.jpg').first()
        if imagen_principal:
            imagen_url = imagen_principal.imagen.url
        else:
            imagen_url = None
        productos_imagen.append((producto, imagen_url))
    return render(request, 'category_filter.html', {
        'productos_imagen': productos_imagen,
        'categoria': categoria,
        'sub_categorias':sub_categorias,
        'cantidad_productos':len(productos)
    })

def subcategoria(request, categoria, sub_categoria):
    productos = Producto.objects.filter(
        sub_categoria__nombre=sub_categoria, 
        sub_categoria__categoria__nombre=categoria
    ).prefetch_related('imagenes')

    orden = request.GET.get('ordenby', 'date')
    if orden == 'price_lower':
        productos = productos.order_by('precio')
    elif orden == 'price_higher':
        productos = productos.order_by('-precio')
    else:
        productos = productos.order_by('-id')

    productos_imagen = []
    for producto in productos:
        imagen_principal = producto.imagenes.filter(imagen__endswith='_1.jpg').first()
        if imagen_principal:
            imagen_url = imagen_principal.imagen.url
        else:
            imagen_url = None
        productos_imagen.append((producto, imagen_url))
    return render(request, 'subcategory_filter.html', {
        'productos_imagen': productos_imagen,
        'categoria': categoria,
        'sub_categoria': sub_categoria,
        'cantidad_productos':len(productos)
    })

def producto_view(request,product_name):
    producto = Producto.objects.get(nombre=product_name)
    return render(request,'producto_view.html',{'producto':producto})