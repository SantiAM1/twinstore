from django.contrib import admin
from .models import CheckOutData, Pedido,Carrito
# Register your models here.
admin.site.register(Pedido)
admin.site.register(Carrito)
admin.site.register(CheckOutData)