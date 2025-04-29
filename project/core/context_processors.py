from django.core.cache import cache
from products.models import Categoria
from django.template.loader import render_to_string
import json

def render_menu(request):
    # data = cache.get('menu_desktop')
    data = {}
    if not data:
        data = {}
        categorias = Categoria.objects.all().prefetch_related('subcategorias').order_by('orden')

        for categoria in categorias:
            seccion_id = categoria.seccion_id

            if seccion_id not in data:
                data[seccion_id] = []
            
            rendered = render_to_string('menus/menu_desktop.html',{'categoria':categoria})
            
            data[seccion_id].append(rendered)

        gaming_menu = render_to_string('menus/gaming_desk.html')

        data['gaming'] = [gaming_menu]
        # cache.set('menu_desktop', data, timeout=60*60)  # cachea por 1 hora

    return {'render_menu': data}