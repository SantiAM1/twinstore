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
            marca, _ = Marca.objects.get_or_create(nombre=fila['Marca'])
            categoria, _ = Categoria.objects.get_or_create(nombre=fila['Categoria'])
            sub_categoria, _ = SubCategoria.objects.get_or_create(nombre=fila['Sub-categoria'], categoria=categoria)

            producto, created = Producto.objects.get_or_create(
                nombre=fila['Producto'],
                defaults={
                    'marca': marca,
                    'categoria': categoria,
                    'sub_categoria': sub_categoria,
                    'precio': fila['Precio'],
                    'descuento': fila['Descuento']
                }
            )

            # Actualiza el producto si ya existía
            if not created:
                producto.precio = fila['Precio']
                producto.descuento = fila['Descuento']
                producto.save()

            # Manejo de atributos adicionales
            # Inalámbrico
            if 'Conectividad' in fila and pd.notna(fila['Conectividad']):
                Atributos.objects.update_or_create(
                    producto=producto,
                    clave='Conectividad',
                    defaults={'valor': fila['Conectividad']}
                )

            # Almacenamiento
            if 'Almacenamiento' in fila and pd.notna(fila['Almacenamiento']):
                Atributos.objects.update_or_create(
                    producto=producto,
                    clave='Almacenamiento',
                    defaults={'valor': fila['Almacenamiento']}
                )
        
        self.stdout.write(self.style.SUCCESS('Productos cargados exitosamente'))