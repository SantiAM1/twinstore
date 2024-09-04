from re import T
from urllib.request import ProxyDigestAuthHandler
from django.db import models
from django.forms import ImageField

class Marca(models.Model):
    nombre = models.CharField(max_length=30)
    imagen = models.ImageField(upload_to='marcas/', default='marcas/default.jpg')

    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=30) 

    def __str__(self):
        return self.nombre

class SubCategoria(models.Model):
    nombre = models.CharField(max_length=30)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='subcategorias', default=1)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=50,unique=True)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    sub_categoria = models.ForeignKey(SubCategoria, on_delete=models.CASCADE, related_name='productos')
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.IntegerField()
    sku = models.CharField(max_length=20, unique=True, blank=True, null=True)  # Nuevo campo SKU

    def __str__(self):
        return self.nombre

class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes',  blank=True)
    imagen = models.ImageField(upload_to='productos_imagenes/')
