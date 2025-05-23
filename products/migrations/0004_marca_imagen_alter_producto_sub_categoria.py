# Generated by Django 5.0.6 on 2024-06-27 14:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_subcategoria_categoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='marca',
            name='imagen',
            field=models.ImageField(default=1, upload_to=''),
        ),
        migrations.AlterField(
            model_name='producto',
            name='sub_categoria',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='productos', to='products.subcategoria'),
        ),
    ]
