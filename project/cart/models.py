from django.db import models
from products.models import Producto
from django.contrib.auth.models import User

class Pedido(models.Model):
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    carrito = models.ForeignKey('Carrito',on_delete=models.CASCADE,related_name="pedidos",default=1)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"
    
    def get_total_precio(self):
        return self.producto.precio * self.cantidad

    def get_prod_img(self):
        return self.producto.imagenes.first().imagen.url if self.producto.imagenes.first() else 'img/prod_default.jpg'
    
    def get_cantidad(self):
        return self.cantidad

class Carrito(models.Model):
    usuario = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carrito de:{self.usuario}" if self.usuario else "Carrito Anonimo"
    
    def agregar_producto(self,producto,cantidad):
        pedido, creado = Pedido.objects.get_or_create(
            producto=producto,
            carrito=self,
            defaults={'cantidad':cantidad}
        )
        if not creado:
            pedido.cantidad += cantidad
            if pedido.cantidad > 5:
                pedido.cantidad = 5
            pedido.save()
        return pedido

    def eliminar_producto(self,producto):
        Pedido.objects.filter(prodcuto=producto,carrito=self).delete()

    def get_total(self):
        return sum(pedido.get_total_precio() for pedido in self.pedidos.all())