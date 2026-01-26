from django.db import models
from products.models import Producto
from django.conf import settings
from django.templatetags.static import static
from products.utils_debug import debug_queries

class Pedido(models.Model):
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    carrito = models.ForeignKey('Carrito',on_delete=models.CASCADE,related_name="pedidos",default=1)
    variante = models.ForeignKey('products.Variante',on_delete=models.CASCADE,blank=True,null=True)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"
    
    @property
    def variante_resumen(self):
        if not self.variante:
            return ""
        
        return self.variante.resumen()

class Carrito(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,blank=True,null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carrito de:{self.usuario}" if self.usuario else "Carrito Anonimo"
    
    def agregar_producto(self,producto,stock:int, variante):
        pedido, creado = Pedido.objects.get_or_create(
            producto=producto,
            carrito=self,
            variante=variante,
            defaults={'cantidad':1}
        )
        if not creado:
            pedido.cantidad += 1
            if pedido.cantidad > stock:
                pedido.cantidad = stock
            pedido.save()
        return pedido

    def eliminar_producto(self,producto):
        Pedido.objects.filter(prodcuto=producto,carrito=self).delete()

    def get_total(self):
        return sum(pedido.get_total_precio() for pedido in self.pedidos.all())

class CheckOutData(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    cupon_id = models.PositiveIntegerField(blank=True,null=True)
    adicional = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    forma_de_pago = models.CharField(max_length=50,blank=True,null=True)
    creado = models.DateTimeField(auto_now_add=True)
    completado = models.BooleanField(default=False)
    descuento = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    mixto = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)

    def __str__(self):
        return f"Checkout de: {self.usuario.username}"