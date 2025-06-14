# Generated by Django 5.1.8 on 2025-06-02 20:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0028_alter_historialcompras_estado_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=6, unique=True)),
                ('descuento', models.DecimalField(decimal_places=2, max_digits=5)),
                ('activo', models.BooleanField(default=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
