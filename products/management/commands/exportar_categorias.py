from django.core.management.base import BaseCommand
from products.models import Categoria, SubCategoria
import json
import os
from django.conf import settings

class Command(BaseCommand):
    help = "Exporta todas las categorías y subcategorías a un archivo JSON."

    def handle(self, *args, **kwargs):
        export_path = os.path.join(settings.BASE_DIR, 'categorias_export.json')
        data = []

        for cat in Categoria.objects.all():
            subcats = SubCategoria.objects.filter(categoria=cat).values(
                'nombre', 'descripcion_seo', 'slug'
            )

            data.append({
                'nombre': cat.nombre,
                'descripcion_seo': cat.descripcion_seo,
                'slug': cat.slug,
                'seccion_id': cat.seccion_id,
                'orden': cat.orden,
                'subcategorias': list(subcats)
            })

        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self.stdout.write(self.style.SUCCESS(f'✅ Categorías exportadas correctamente a {export_path}'))
