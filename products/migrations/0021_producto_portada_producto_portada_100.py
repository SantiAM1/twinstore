# Generated by Django 5.1.7 on 2025-04-14 19:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0020_producto_precio_anterior'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='portada',
            field=models.ImageField(blank=True, null=True, upload_to='productos/'),
        ),
        migrations.AddField(
            model_name='producto',
            name='portada_100',
            field=models.ImageField(blank=True, null=True, upload_to='productos/100/'),
        ),
    ]
