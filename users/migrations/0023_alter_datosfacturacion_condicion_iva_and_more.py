# Generated by Django 5.1.10 on 2025-07-08 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0022_remove_datosfacturacion_tipo_factura_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datosfacturacion',
            name='condicion_iva',
            field=models.CharField(choices=[('A', 'Resp Insc.'), ('B', 'Consumidor final'), ('C', 'Mono')], max_length=1),
        ),
        migrations.AlterField(
            model_name='perfilusuario',
            name='condicion_iva',
            field=models.CharField(choices=[('A', 'Resp Insc.'), ('B', 'Consumidor final'), ('C', 'Mono')], max_length=1),
        ),
    ]
