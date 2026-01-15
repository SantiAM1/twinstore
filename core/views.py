from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.http import HttpRequest
from django.core.cache import cache
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import cache_page
from django.utils import timezone

from .throttling import PrediccionBusquedaThrottle
from .utils import get_configuracion_tienda
from .forms import ExcelUploadForm,DolarActualizar
from .permissions import BloquearSiMantenimiento
from .models import Tienda

from products.models import Producto, Marca, SubCategoria, Atributo,Etiquetas

from rest_framework.views import APIView
from rest_framework.response import Response

import pandas as pd
import uuid
import re
from decimal import Decimal, InvalidOperation
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
        q = request.GET.get('q', '').strip()
        if not q or len(q) < 2:
            return Response([])

        q = normalize_text(q)
        tokens = [t for t in q.replace("-", " ").split() if t]

        productos = cache.get('productos_busqueda')

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

            cache.set('productos_busqueda', productos, 300)

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

def home(request):
    home_cache = cache.get('home_cache')
    if not home_cache:
        home_cache = {
            'ofertas': Producto.objects.filter(descuento__gt=0).prefetch_related("colores__imagenes_color","imagenes_producto"),
            'destacados': Producto.objects.filter(etiquetas__slug='destacado').prefetch_related("colores__imagenes_color","imagenes_producto"),
        }
        cache.set('home_cache', home_cache, 60 * 30)

    return render(request,'core/inicio.html', {'destacados': home_cache['destacados'], 'ofertas': home_cache['ofertas']})

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
    cache.delete('modo_mantenimiento')
    if config.mantenimiento:
        messages.success(request, "El sitio ha sido puesto en modo mantenimiento.")
    else:
        messages.success(request, "El sitio ha sido quitado del modo mantenimiento.")
    return redirect(request.META.get('HTTP_REFERER', 'admin:index'))