from django.core.management.base import BaseCommand
from products.models import Producto, ImagenProducto
import os
import re
from django.core.files.images import ImageFile

class Command(BaseCommand):
    help = 'Carga imágenes de productos desde una carpeta general sin duplicaciones y asigna portada según el formato imagen_01.jpg'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help='Ruta base donde se encuentran las imágenes')

    def handle(self, *args, **options):
        ruta_base = options['path'] if options['path'] else 'media/productos/'

        for producto in Producto.objects.all():
            ruta_sku = os.path.join(ruta_base, producto.sku)

            if os.path.exists(ruta_sku):
                imagenes_existentes = set(ImagenProducto.objects.filter(producto=producto).values_list('imagen', flat=True))
                
                # 🔹 Ordenamos las imágenes según el formato "imagen_XX.jpg"
                def orden_imagenes(nombre):
                    match = re.match(r"imagen_(\d{2})\.(jpg|png|jpeg)", nombre, re.IGNORECASE)
                    return int(match.group(1)) if match else 999  # Las imágenes sin número irán al final

                imagenes_nuevas = sorted(os.listdir(ruta_sku), key=orden_imagenes)

                for index, filename in enumerate(imagenes_nuevas):
                    ruta_completa = os.path.join(ruta_sku, filename)

                    if filename not in imagenes_existentes:
                        with open(ruta_completa, 'rb') as f:
                            imagen = ImageFile(f, name=f"productos_imagenes/{filename}")
                            imagen_producto = ImagenProducto(producto=producto, imagen=imagen)
                            imagen_producto.save()
                            
                            # ✅ Mensaje en consola indicando la portada
                            if index == 0:
                                self.stdout.write(self.style.SUCCESS(f'✔ Portada asignada: {filename} para {producto.sku}'))
                            else:
                                self.stdout.write(self.style.SUCCESS(f'Imagen {filename} cargada para {producto.sku}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Imagen {filename} ya existe, no se carga de nuevo.'))
