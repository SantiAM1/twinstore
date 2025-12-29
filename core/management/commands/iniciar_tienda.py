from django.core.management.base import BaseCommand
from core.models import Tienda
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from products.models import Proveedor

class Command(BaseCommand):
    help = 'Inicia la tienda configurando los parámetros iniciales'

    def handle(self, *args, **kwargs):
        # Aquí puedes agregar la lógica para iniciar la tienda
        Tienda.objects.get_or_create()
        Proveedor.objects.get_or_create(nombre='Generico')
        gestores_group = Group.objects.create(name='Gestores')
        staff_user = User.objects.create_user(username='gestor@ts.ar', password='admin123', is_staff=True)
        staff_user.groups.add(gestores_group)

        User.objects.create_superuser(username='superadmin@ts.ar', password='superadmin123', is_superuser=True, is_staff=True)

        self.stdout.write(self.style.SUCCESS('Tienda iniciada correctamente'))