# Generated by Django 5.1.8 on 2025-05-01 01:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0042_categoria_orden_alter_categoria_seccion_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categoria',
            name='seccion_id',
            field=models.CharField(blank=True, choices=[('componentes', 'Componentes'), ('computos', 'PC y Notebooks'), ('accesorios', 'Accesorios'), ('dispositivos', 'Dispositivos'), ('impresion', 'Impresión')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='subcategoria',
            name='categoria',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategorias', to='products.categoria'),
        ),
    ]
