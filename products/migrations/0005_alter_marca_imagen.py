# Generated by Django 5.0.6 on 2024-06-27 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_marca_imagen_alter_producto_sub_categoria'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marca',
            name='imagen',
            field=models.ImageField(default='path/to/default/image.jpg', upload_to='marcas/'),
        ),
    ]
