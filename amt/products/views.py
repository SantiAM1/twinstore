from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse,JsonResponse
from .models import Producto, SubCategoria,Categoria, Atributos,Marca
from django.urls import reverse

# Create your views here.

def test(request):
    url_marca = request.GET.getlist('marca')
    url_atri = request.GET.getlist('Conectividad')
    print(url_atri)

    productos = Producto.objects.filter(categoria__nombre='Perifericos')
    marcas = set(producto.marca for producto in productos)
    atributos_dict = dict()
    for producto in productos:
        for atributo in producto.atributos.all():
            atributos_dict.update({f'{atributo.valor}':f'{atributo.clave}'})
            clave = atributo.clave
    context = {
        'productos':productos,
        'marcas':marcas,
        'atributos_dict':atributos_dict,
        'clave':clave,
        'url_marca':url_marca,
        'url_atri':url_atri
    }
    return render(request,'test.html',context)

def por_categoria(request, categoria_nombre):
    productos = Producto.objects.filter(categoria__nombre=categoria_nombre)
    categoria = get_object_or_404(Categoria, nombre=categoria_nombre)
    subcategorias = categoria.subcategorias.all()
    urls_subcategorias = {subcategoria.nombre:subcategoria.nombre for subcategoria in subcategorias}
    context = {
        'productos':productos,
        'categoria':categoria,
        'subcategorias':subcategorias,
        'marcas':set(producto.marca for producto in productos),
        'url_categoria':reverse('products:categoria_filter',kwargs={'categoria_nombre':categoria_nombre}),
        'urls_subcategorias':urls_subcategorias
    }
    return render(request, 'category_filter.html', context)

def por_subcategoria(request, categoria_nombre, subcategoria_nombre):
    subcategoria = get_object_or_404(SubCategoria, nombre=subcategoria_nombre, categoria__nombre=categoria_nombre)
    productos = Producto.objects.filter(
        sub_categoria__nombre=subcategoria_nombre,
        )
    categoria = subcategoria.categoria

    atributos_dict = dict()
    for producto in productos:
        for atributo in producto.atributos.all():
            atributos_dict.update({f'{atributo.valor}':f'{atributo.clave}'})
            clave = atributo.clave
    if len(atributos_dict) == 1:
        atributos_dict = dict()
    context = {
        'productos': productos,
        'subcategoria': subcategoria,
        'categoria': categoria,
        'marcas': set(producto.marca for producto in productos),
        'url_categoria': reverse('products:categoria_filter', kwargs={'categoria_nombre': categoria_nombre}),
        'url_subcategoria': reverse('products:subcategoria_filter', kwargs={'categoria_nombre': categoria_nombre, 'subcategoria_nombre': subcategoria_nombre}),
        'atributos_dict':atributos_dict,
        'clave':clave,
    }
    return render(request, 'subcategory_filter.html', context)
