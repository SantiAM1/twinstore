from rest_framework import serializers
from django.core import signing
from django.shortcuts import get_object_or_404
from products.models import Producto, Variante
import re

class AgregarAlCarritoSerializer(serializers.Serializer):
    producto_id = serializers.CharField()
    sku = serializers.CharField(required=False, allow_null=True)

    def validate(self, data):
        try:
            prod_id = signing.loads(data['producto_id'])
            producto = Producto.objects.get(id=prod_id)
        except signing.BadSignature:
            raise serializers.ValidationError("ID de producto invalido o manipulado")
        except Producto.DoesNotExist:
            raise serializers.ValidationError("El producto no existe")
        
        sku = data.get('sku')
        variante_obj = None

        if producto.variantes.exists():
            if not sku:
                raise serializers.ValidationError("Este producto requiere seleccionar opciones (Color/Talle).")
            try:
                variante_obj = producto.variantes.get(sku=sku)
            except Variante.DoesNotExist:
                raise serializers.ValidationError(f"La variante {sku} no es válida para este producto.")
        else:
            if sku:
                raise serializers.ValidationError("Este producto no tiene variantes.")
        
        data['producto_obj'] = producto
        data['variante_obj'] = variante_obj
        
        return data

class EliminarPedidoSerializer(serializers.Serializer):
    pedido_id = serializers.CharField()

class ActualizarPedidoSerializer(serializers.Serializer):
    pedido_id = serializers.CharField()
    action = serializers.ChoiceField(choices=["mas", "menos"])