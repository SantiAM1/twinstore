from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
import json

class Command(BaseCommand):
    help = 'Exporta los permisos de un grupo específico'

    def add_arguments(self, parser):
        parser.add_argument('group_name', type=str, help='Nombre del grupo')

    def handle(self, *args, **kwargs):
        group_name = kwargs['group_name']
        try:
            group = Group.objects.get(name=group_name)
            permissions = list(group.permissions.values_list('codename', flat=True))
            
            # Guardamos en un archivo JSON
            with open(f'{group_name}_permisos.json', 'w') as f:
                json.dump(permissions, f, indent=4)
            
            self.stdout.write(self.style.SUCCESS(f'Permisos exportados correctamente a {group_name}_permisos.json'))
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR('El grupo no existe'))
