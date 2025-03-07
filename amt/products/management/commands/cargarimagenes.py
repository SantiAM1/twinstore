from django.core.management.base import BaseCommand
from products.models import Producto, ImagenProducto
import os
from django.core.files.images import ImageFile

class Command(BaseCommand):
    help = 'Carga imágenes de productos desde una estructura de directorios basada en SKUs'

    def add_arguments(self, parser):
        # - Opcional: Agregar argumentos al comando si es necesario, por ejemplo, especificar un path base
        parser.add_argument('--path', type=str, help='Ruta base donde se encuentran las carpetas de SKUs')

    def handle(self, *args, **options):
        ruta_base = options['path'] if options['path'] else 'media/productos/'
        for producto in Producto.objects.all():
            ruta_sku = os.path.join(ruta_base, producto.sku)
            if os.path.exists(ruta_sku):
                for filename in os.listdir(ruta_sku):
                    ruta_completa = os.path.join(ruta_sku, filename)
                    # ! Verificar si la imagen ya existe para el producto
                    if not ImagenProducto.objects.filter(producto=producto, imagen=filename).exists():
                        with open(ruta_completa, 'rb') as f:
                            imagen = ImageFile(f, name=filename)
                            imagen_producto = ImagenProducto(producto=producto, imagen=imagen)
                            imagen_producto.save()
                            self.stdout.write(self.style.SUCCESS(f'Imagen {filename} cargada para el producto {producto.sku}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Imagen {filename} ya existe, no se carga de nuevo.'))
