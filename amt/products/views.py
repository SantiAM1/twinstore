from ast import Sub
from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse,JsonResponse
from .models import Producto, SubCategoria,Categoria,Marca
from django.urls import reverse

# Create your views here.

def categoria(request, categoria):
    sub_categorias = SubCategoria.objects.filter(categoria__nombre=categoria)
    productos = Producto.objects.filter(sub_categoria__in=sub_categorias).prefetch_related('imagenes')

    productos=ordenby(request,productos)
    productos_imagen=get_prod_img(productos)

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

    productos=ordenby(request,productos)
    productos_imagen=get_prod_img(productos)

    return render(request, 'subcategory_filter.html', {
        'productos_imagen': productos_imagen,
        'categoria': categoria,
        'sub_categoria': sub_categoria,
        'cantidad_productos':len(productos)
    })

def producto_view(request,product_name):
    producto = Producto.objects.get(nombre=product_name)
    imagenes = producto.imagenes.all()
    template_path = f'products-specs/{producto.sku}.html'
    return render(request,'producto_view.html',{
        'producto':producto,
        'template_path':template_path,
        'imagenes':imagenes
        })

def ordenby(request, productos):
    orden = request.GET.get('ordenby', 'date')
    if orden == 'price_lower':
        productos = productos.order_by('precio')
    elif orden == 'price_higher':
        productos = productos.order_by('-precio')
    else:
        productos = productos.order_by('-id')
    
    return productos

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