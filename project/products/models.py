from re import T
from django.db import models

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
    precio_anterior = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    descuento = models.IntegerField(default=0)
    sku = models.CharField(max_length=20, unique=True, blank=True, null=True)
    portada = models.ImageField(upload_to='productos/',null=True, blank=True)
    portada_100 = models.ImageField(upload_to='productos/100/', null=True, blank=True)

    def __str__(self):
        return self.nombre

class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes',  blank=True)
    imagen = models.ImageField(upload_to='productos_imagenes/')

class Atributo(models.Model):
    producto = models.ForeignKey(Producto, related_name="atributos", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    valor = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}: {self.valor}"
    
class CategoriaEspecificacion(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class EspecificacionTecnica(models.Model):
    producto = models.ForeignKey(Producto, related_name='especificaciones', on_delete=models.CASCADE)
    categoria = models.ForeignKey(CategoriaEspecificacion, on_delete=models.SET_NULL, null=True, blank=True)
    datos = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.categoria.nombre} ({self.producto.nombre})"