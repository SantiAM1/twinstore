from django.db import models
from products.models import Producto
from django.contrib.auth.models import User

class Pedido(models.Model):
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

class Carrito(models.Model):
    usuario = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True)
    pedidos = models.ManyToManyField(Pedido)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Recopilar la lista de pedidos en el carrito
        pedidos_str = ", ".join([f"{pedido.cantidad}x {pedido.producto.nombre}" for pedido in self.pedidos.all()])
        return f"{self.usuario} - Pedidos: {pedidos_str}" if pedidos_str else f"{self.usuario} - Carrito vacío"