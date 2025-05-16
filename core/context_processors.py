from django.conf import settings
from django.core.cache import cache
from products.models import Categoria
from django.template.loader import render_to_string
import json
from django_user_agents.utils import get_user_agent

def canonical_url(request):
    """Genera la canonical URL limpia, sin parámetros GET"""
    scheme = "https" if request.is_secure() else "http"
    domain = request.get_host()
    path = request.path
    print(f"{scheme}://{domain}{path}")
    return {
        "canonical_url": f"{scheme}://{domain}{path}"
    }

def render_menu(request):
    ORDEN_SECCIONES = ["Componentes", "PC y Notebooks", "Accesorios", "Móviles", "Impresión"]
    SECCIONES_LABEL = {
        'componentes': 'Componentes',
        'computos': 'PC y Notebooks',
        'accesorios': 'Accesorios',
        'moviles': 'Móviles',
        'impresion': 'Impresión',
    }
    data_desk = cache.get('menu_desktop')
    data_mob = cache.get('menu_mobile')
    data_desk = {}
    if not data_desk or not data_mob:
        data_desk = {}
        data_mob = {}
        categorias = Categoria.objects.all().prefetch_related('subcategorias').order_by('orden')
        for categoria in categorias:
            seccion_id = categoria.seccion_id
            seccion_label = SECCIONES_LABEL.get(seccion_id, seccion_id)

            if seccion_id not in data_desk:
                data_desk[seccion_id] = []
            if seccion_label not in data_mob:
                data_mob[seccion_label] = []

            # * PC
            rendered_desk = render_to_string('menus/menu_desktop.html',{'categoria':categoria})
            data_desk[seccion_id].append(rendered_desk)

            # * MOBILE
            rendered_mob = render_to_string('menus/mobile_category.html',{'categoria':categoria})
            data_mob[seccion_label].append(rendered_mob)

        gaming_menu = render_to_string('menus/gaming_desk.html')
        data_desk['gaming'] = [gaming_menu]

        cache.set('menu_desktop', data_desk, timeout=60*60)
        cache.set('menu_mobile', data_mob, timeout=60*60)

    data_mobile = {key: data_mob[key] for key in ORDEN_SECCIONES if key in data_mob}

    return {'render_menu': data_desk,'render_menu_mobile':data_mobile}