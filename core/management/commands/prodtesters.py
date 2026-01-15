from django.core.management.base import BaseCommand
from products.models import Producto, Marca, Etiquetas

class Command(BaseCommand):
    help = 'Inicia la tienda configurando los parámetros iniciales'

    def handle(self, *args, **kwargs):
        marca, _ = Marca.objects.get_or_create(nombre='Logitech')
        etiqueta, _ = Etiquetas.objects.get_or_create(nombre='Descuento')
        Producto.objects.get_or_create(nombre='Producto 1', precio_divisa=100, marca=marca)
        Producto.objects.get_or_create(nombre='Producto 2', precio_divisa=200, marca=marca, descuento=10)
        Producto.objects.get_or_create(nombre='Producto 3', precio_divisa=300, marca=marca, etiquetas=etiqueta)

        self.stdout.write(self.style.SUCCESS('Productos de prueba creados correctamente'))