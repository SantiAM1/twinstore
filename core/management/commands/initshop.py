from django.core.management.base import BaseCommand
from core.models import Tienda
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.models import User
from products.models import Proveedor, SubCategoria, Categoria, Marca, Etiquetas, Producto
import json
import os
from django.conf import settings
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Inicia la tienda configurando los parámetros iniciales'

    def add_arguments(self, parser):
        parser.add_argument('--products', action='store_true', help='Crear productos de ejemplo')

    def handle(self, *args, **kwargs):
        steps = 3 if not kwargs['products'] else 4
        # Aquí puedes agregar la lógica para iniciar la tienda
        Tienda.objects.get_or_create()
        Proveedor.objects.get_or_create(nombre='Generico')
        gestores_group, _ = Group.objects.get_or_create(name='Gestores')

        if not User.objects.exists():
            staff_user = User.objects.create_user(username='gestor@ts.ar', password='admin123', is_staff=True, email='gestor@ts.ar')
            admin = User.objects.create_superuser(username='superadmin@ts.ar', password='superadmin123', is_superuser=True, is_staff=True, email='superadmin@ts.ar')
            staff_user.groups.add(gestores_group)
            staff_user.perfil.email_verificado = True
            admin.perfil.email_verificado = True
            staff_user.perfil.save()
            admin.perfil.save()

        self.stdout.write(self.style.SUCCESS(f'✅ (1/{steps}) Tienda iniciada correctamente'))

        json_file = "Gestores_permisos.json"

        if not os.path.exists(json_file):
            self.stdout.write(self.style.ERROR('El archivo JSON no existe'))
            return

        with open(json_file, 'r') as f:
            codenames = json.load(f)

        for codename in codenames:
            try:
                permiso = Permission.objects.get(codename=codename)
                gestores_group.permissions.add(permiso)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Permiso no encontrado: {codename}"))

        self.stdout.write(self.style.SUCCESS(f'✅ (2/{steps}) Permisos importados correctamente al grupo "Gestores"'))

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

        self.stdout.write(self.style.SUCCESS(f"✅ (3/{steps}) Categorías importadas correctamente."))

        if kwargs['products']:
            marca, _ = Marca.objects.get_or_create(nombre='Logitech')
            etiqueta, _ = Etiquetas.objects.get_or_create(nombre='destacados')
            Producto.objects.get_or_create(nombre='Producto 1', precio_divisa=100, marca=marca)
            Producto.objects.get_or_create(nombre='Producto 2', precio_divisa=200, marca=marca, descuento=10)
            producto3, _ = Producto.objects.get_or_create(nombre='Producto 3', precio_divisa=300, marca=marca)
            producto3.etiquetas.set([etiqueta])

            self.stdout.write(self.style.SUCCESS(f"✅ (4/{steps}) Productos de prueba creados correctamente"))
