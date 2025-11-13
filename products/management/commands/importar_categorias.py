from django.core.management.base import BaseCommand
from products.models import Categoria, SubCategoria
from django.utils.text import slugify
import json
import os
from django.conf import settings

class Command(BaseCommand):
    help = "Importa categorías y subcategorías desde un archivo JSON."

    def handle(self, *args, **kwargs):
        import_path = os.path.join(settings.BASE_DIR, 'categorias_export.json')

        if not os.path.exists(import_path):
            self.stdout.write(self.style.ERROR("❌ El archivo de importación no existe."))
            return

        with open(import_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            categoria, _ = Categoria.objects.get_or_create(
                nombre=item['nombre'],
                defaults={
                    'descripcion_seo': item['descripcion_seo'],
                    'slug': item.get('slug') or slugify(item['nombre']),
                }
            )

            for sub in item.get('subcategorias', []):
                SubCategoria.objects.get_or_create(
                    nombre=sub['nombre'],
                    categoria=categoria,
                    defaults={
                        'descripcion_seo': sub['descripcion_seo'],
                        'slug': sub.get('slug') or slugify(sub['nombre'])
                    }
                )

        self.stdout.write(self.style.SUCCESS("✅ Categorías importadas correctamente."))
