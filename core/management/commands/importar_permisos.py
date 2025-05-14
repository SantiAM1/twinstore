from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
import json
import os

class Command(BaseCommand):
    help = 'Importa permisos a un grupo específico desde un archivo JSON'

    def add_arguments(self, parser):
        parser.add_argument('group_name', type=str, help='Nombre del grupo')
        parser.add_argument('json_file', type=str, help='Ruta al archivo JSON con los permisos')

    def handle(self, *args, **kwargs):
        group_name = kwargs['group_name']
        json_file = kwargs['json_file']

        if not os.path.exists(json_file):
            self.stdout.write(self.style.ERROR('El archivo JSON no existe'))
            return

        with open(json_file, 'r') as f:
            codenames = json.load(f)

        grupo, creado = Group.objects.get_or_create(name=group_name)

        for codename in codenames:
            try:
                permiso = Permission.objects.get(codename=codename)
                grupo.permissions.add(permiso)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Permiso no encontrado: {codename}"))

        self.stdout.write(self.style.SUCCESS(f'Permisos importados correctamente al grupo "{group_name}"'))
