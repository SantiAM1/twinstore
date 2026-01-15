from django.core.management.base import BaseCommand
from core.models import Tienda
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from products.models import Proveedor

class Command(BaseCommand):
    help = 'Inicia la tienda configurando los parámetros iniciales'

    def handle(self, *args, **kwargs):
        Tienda.objects.get_or_create()
        Proveedor.objects.get_or_create(nombre='Generico')
        gestores_group = Group.objects.create(name='Gestores')
        staff_user = User.objects.create_user(username='gestor@ts.ar', password='admin123', is_staff=True, email='gestor@ts.ar')
        staff_user.groups.add(gestores_group)

        admin = User.objects.create_superuser(username='superadmin@ts.ar', password='superadmin123', is_superuser=True, is_staff=True, email='superadmin@ts.ar')

        staff_user.perfil.email_verificado = True
        admin.perfil.email_verificado = True
        staff_user.perfil.save()
        admin.perfil.save()
    
        self.stdout.write(self.style.SUCCESS('Tienda iniciada correctamente'))