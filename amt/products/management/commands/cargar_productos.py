from django.core.management.base import BaseCommand
import pandas as pd
from products.models import Producto, Marca, Categoria, SubCategoria, Atributos

class Command(BaseCommand):
    help = 'Carga productos desde un archivo Excel'

    def handle(self, *args, **options):
        ruta = 'C:/Users/Santiago/Desktop/Amt/server/Lista.xlsx'
        df = pd.read_excel(ruta)
        
        if df.empty:
            self.stdout.write(self.style.ERROR('El archivo Excel está vacío'))
            return

        for _, fila in df.iterrows():
            # Obtiene o crea la marca
            marca, _ = Marca.objects.get_or_create(nombre=fila['Marca'])

            # Obtiene la subcategoría y su categoría asociada
            try:
                sub_categoria = SubCategoria.objects.get(nombre=fila['Sub-categoria'])
                categoria = sub_categoria.categoria  # Obtiene la categoría vinculada a la subcategoría
            except SubCategoria.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'La subcategoría "{fila["Sub-categoria"]}" no existe en la base de datos'))
                continue

            # Genera un SKU único
            sku = f"{marca.nombre[:3].upper()}-{sub_categoria.nombre[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"

            # Crea o actualiza el producto
            producto, created = Producto.objects.get_or_create(
                nombre=fila['Producto'],
                defaults={
                    'marca': marca,
                    'sub_categoria': sub_categoria,
                    'precio': fila['Precio'],
                    'descuento': fila['Descuento'],
                    'sku': sku
                }
            )

            # Actualiza el producto si ya existía
            if not created:
                producto.precio = fila['Precio']
                producto.descuento = fila['Descuento']
                # Solo asigna un SKU si aún no existe
                if not producto.sku:
                    producto.sku = sku
                producto.save()
        
        self.stdout.write(self.style.SUCCESS('Productos cargados exitosamente'))