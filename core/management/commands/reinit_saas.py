import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.db import connection

class Command(BaseCommand):
    help = 'Limpia ABSOLUTAMENTE TODOS los esquemas y recrea la estructura de Twinstore'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stdout.write(self.style.ERROR('Este comando solo se puede usar en modo DEBUG.'))
            return

        self.stdout.write(self.style.WARNING('--- INICIANDO DESTRUCCIÓN TOTAL DE ESQUEMAS ---'))

        with connection.cursor() as cursor:
            # 1. Buscamos todos los esquemas que NO sean del sistema (pg_ e information_schema)
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT LIKE 'pg_%%' 
                AND schema_name != 'information_schema';
            """)
            schemas = [row[0] for row in cursor.fetchall()]

            # 2. Los borramos todos con CASCADE
            for schema in schemas:
                self.stdout.write(f"Borrando esquema: {schema}...")
                # Usamos identificadores entre comillas dobles por si hay nombres raros
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE;')

            # 3. Recreamos el esquema public (obligatorio para Django)
            self.stdout.write("Recreando esquema 'public' limpio...")
            cursor.execute("CREATE SCHEMA public;")
        
        # 4. Migraciones SHARED (Esto creará las tablas de Clientes/Dominios/Users en public)
        self.stdout.write("Migrando aplicaciones compartidas (Core)...")
        call_command('migrate_schemas', shared=True, interactive=False)

        # 5. Configuración de Tenant Público
        from customers.models import Client, Domain
        self.stdout.write("Configurando dominio principal (localhost)...")
        
        tenant = Client.objects.create(
            schema_name='public',
            name='Twinstore Admin'
        )
        
        Domain.objects.create(
            tenant=tenant,
            domain='localhost', 
            is_primary=True
        )

        nike = Client.objects.create(
            schema_name='nike',
            name='Nike'
        )

        Domain.objects.create(
            tenant=nike,
            domain='nike.localhost', 
            is_primary=True
        )

        # 6. Crear tu Superusuario (Ajustado a tu Manager de Email)
        # ...

        self.stdout.write(self.style.SUCCESS('-----------------------------------------'))
        self.stdout.write(self.style.SUCCESS('¡LISTO! Sistema reseteado.'))
        self.stdout.write(self.style.SUCCESS('URL: http://localhost:8000/admin'))
