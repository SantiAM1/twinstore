from django.core.cache import cache
from products.models import Categoria
from django.template.loader import render_to_string
import json
from django_user_agents.utils import get_user_agent

def render_menu(request):
    ORDEN_SECCIONES = ["componentes", "computos", "accesorios", "dispositivos", "impresion"]
    data_desk = cache.get('menu_desktop')
    data_mob = cache.get('menu_mobile')
    if not data_desk or not data_mob:
        data_desk = {}
        data_mob = {}
        categorias = Categoria.objects.all().prefetch_related('subcategorias').order_by('orden')
        for categoria in categorias:
            seccion_id = categoria.seccion_id

            if seccion_id not in data_desk:
                data_desk[seccion_id] = []
            if seccion_id not in data_mob:
                data_mob[seccion_id] = []

            # * PC
            rendered_desk = render_to_string('menus/menu_desktop.html',{'categoria':categoria})
            data_desk[seccion_id].append(rendered_desk)

            # * MOBILE
            rendered_mob = render_to_string('menus/mobile_category.html',{'categoria':categoria})
            data_mob[seccion_id].append(rendered_mob)

        gaming_menu = render_to_string('menus/gaming_desk.html')
        data_desk['gaming'] = [gaming_menu]

        cache.set('menu_desktop', data_desk, timeout=60*60)
        cache.set('menu_mobile', data_mob, timeout=60*60)

    data_mobile = {key: data_mob[key] for key in ORDEN_SECCIONES if key in data_mob}

    return {'render_menu': data_desk,'render_menu_mobile':data_mobile}