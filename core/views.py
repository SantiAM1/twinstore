from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpRequest
from django.core.cache import cache
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import cache_page
from .utils import gen_cache_key

from .throttling import PrediccionBusquedaThrottle
from .utils import get_configuracion_tienda
from .permissions import BloquearSiMantenimiento
from .models import Tienda,HomeSection, HomeProductGrid

from products.models import Producto

from rest_framework.views import APIView
from rest_framework.response import Response

import unicodedata
# Create your views here.

@cache_page(60 * 15)
def contacto(request):
    return render(request,'core/contacto.html')

@cache_page(60 * 15)
def politicas_tecnico(request):
    return render(request,'core/politicas/politicas-tecnico.html')

@cache_page(60 * 15)
def boton_arrepentimiento(request):
    return render(request,'core/politicas/arrepentimiento.html')

@cache_page(60 * 15)
def terminos_condiciones(request):
    return render(request,'core/politicas/terminos-condiciones.html')

@cache_page(60 * 15)
def preguntas_frecuentes(request):
    return render(request,'core/politicas/faq.html')

@cache_page(60 * 15)
def politicas_envios(request):
    return render(request, 'core/politicas/politicas-envios.html')

@cache_page(60 * 15)
def politicas_devolucion(request):
    return render(request,'core/politicas/politicas-devolucion.html')

@cache_page(60 * 15)
def politicas_priv(request):
    return render(request,'core/politicas/politicas-privacidad.html')

def pagina_mantenimiento(request):
    return render(request, 'core/mantenimiento.html')

def normalize_text(text: str) -> str:
    """
    Normaliza texto eliminando tildes, símbolos y lower-case.
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    return text.lower()


class BusquedaPredictivaView(APIView):
    throttle_classes = [PrediccionBusquedaThrottle]
    permission_classes = [BloquearSiMantenimiento]
    

    def get(self, request):
        CACHE_KEY = gen_cache_key('productos_busqueda',request)
        q = request.GET.get('q', '').strip()
        if not q or len(q) < 2:
            return Response([])

        q = normalize_text(q)
        tokens = [t for t in q.replace("-", " ").split() if t]

        productos = cache.get(CACHE_KEY)

        if not productos:
            productos_raw = list(
                Producto.objects
                .values(
                    'nombre',
                    'slug',
                    'imagenes_producto__imagen_200',
                    'precio_final',
                )
                .order_by('-precio_final')
            )

            productos_dict = {}
            for p in productos_raw:
                slug = p['slug']
                if slug not in productos_dict:
                    productos_dict[slug] = p

            productos = list(productos_dict.values())

            for p in productos:
                img = p.get('imagenes_producto__imagen_200')
                if img:
                    p['imagenes_producto__imagen_200'] = f"{settings.MEDIA_URL}{img}"

                p["search"] = normalize_text(f"{p['nombre']} {p['slug']}")

            cache.set(CACHE_KEY, productos, 300)

        resultados = []
        for p in productos:
            search = p['search']
            score = 0

            for token in tokens:
                if token == search:
                    score += 50  # coincidencia perfecta
                elif token in search.split():
                    score += 25  # palabra exacta
                elif search.startswith(token):
                    score += 15  # prefix
                elif token in search:
                    score += 10  # substring

            if score > 0:
                p['_score'] = score
                resultados.append(p)

        resultados.sort(
            key=lambda x: (x['_score'], x['precio_final'], bool(x["imagenes_producto__imagen_200"])),
            reverse=True
        )

        return Response(resultados[:10])

def home(request: HttpRequest):
    CACHE_KEY = gen_cache_key('home_secciones_data',request)
    CACHE_TIMEOUT = 60 * 15

    secciones = cache.get(CACHE_KEY)

    if not secciones:
        print("⚡ Cache miss: Consultando a la Base de Datos...")
        
        secciones_qs = HomeSection.objects.filter(activo=True).order_by('orden').prefetch_related(
            'banners',
            'banners_medios',
            'grids_productos',
            # Optimizaciones Bento/Carousel
            'categorias__producto__imagenes_producto',
            'categorias__producto__etiquetas',
            'categorias__categoria',
            'categorias__subcategoria__categoria',
            'categorias__marca',
            # Optimizaciones Bento Estático
            'static_bento__producto__imagenes_producto',
            'static_bento__producto__etiquetas',
            'static_bento__categoria',
            'static_bento__subcategoria__categoria',
            'static_bento__marca',
        )

        secciones = list(secciones_qs)

        base_products_qs = Producto.objects.all().select_related(
            'marca', 'sub_categoria', 'evento'
        ).prefetch_related(
            'colores__imagenes_color', 'imagenes_producto', 'etiquetas'
        )

        for seccion in secciones:
            if seccion.tipo == HomeSection.Tipo.GRILLA:
                grids = list(seccion.grids_productos.all())
                
                if grids:
                    grid = grids[0]
                    productos = []

                    if grid.criterio == HomeProductGrid.Criterio.DESTACADOS:
                        productos = base_products_qs.filter(etiquetas__slug='destacados')
                    elif grid.criterio == HomeProductGrid.Criterio.OFERTAS:
                        productos = base_products_qs.filter(descuento__gt=0)
                    elif grid.criterio == HomeProductGrid.Criterio.MARCA:
                        if grid.marca_filtro_id:
                            productos = base_products_qs.filter(marca_id=grid.marca_filtro_id)
                    elif grid.criterio == HomeProductGrid.Criterio.ETIQUETA:
                        if grid.etiqueta_filtro_id:
                            productos = base_products_qs.filter(etiquetas__id=grid.etiqueta_filtro_id)
                    elif grid.criterio == HomeProductGrid.Criterio.RECIENTES:
                        productos = base_products_qs.order_by('-updated_at')[:12]
                    elif grid.criterio == HomeProductGrid.Criterio.EVENTO:
                        from core.models import EventosPromociones
                        evento = EventosPromociones.objects.first()
                        if evento and evento.esta_activo:
                            productos = base_products_qs.filter(evento=evento)
                        else:
                            productos = base_products_qs.order_by('-updated_at')[:12]

                    seccion.productos_list = list(productos) if productos is not None else []

        cache.set(CACHE_KEY, secciones, CACHE_TIMEOUT)
    else:
        print("🚀 Cache hit: Usando datos de memoria")

    return render(request, 'core/home.html', {
        'secciones': secciones
    })

@staff_member_required
def cache_clear(request):
    cache.clear()
    messages.success(request, "Cache limpiada correctamente.")
    return redirect('core:home')

@staff_member_required
def test(request):

    messages.info(request,"Esto es un mensaje de prueba.")
    messages.success(request, "Mensaje de exito!")
    messages.error(request, "Mensaje de error")

    return render(request, "core/test.html", {})

@staff_member_required
def toggle_mantenimiento(request: HttpRequest):
    config = Tienda.objects.first()
    if not config:
        config = Tienda.objects.create()
    config.mantenimiento = not config.mantenimiento
    config.save()
    MANTENIMIENTO_CACHE_KEY = gen_cache_key('modo_mantenimiento',request)
    cache.delete(MANTENIMIENTO_CACHE_KEY)
    if config.mantenimiento:
        messages.success(request, "El sitio ha sido puesto en modo mantenimiento.")
    else:
        messages.success(request, "El sitio ha sido quitado del modo mantenimiento.")
    return redirect(request.META.get('HTTP_REFERER', 'admin:index'))