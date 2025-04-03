from rest_framework import serializers

class CalcularPedidoSerializer(serializers.Serializer):
    metodo_pago = serializers.CharField()
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    email = serializers.EmailField()
    dni_cuit = serializers.CharField()
    tipo_factura = serializers.CharField()
    calle = serializers.CharField()
    cuidad = serializers.CharField()
    codigo_postal = serializers.CharField()
    recibir_mail = serializers.BooleanField()

class AgregarAlCarritoSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField()

class EliminarPedidoSerializer(serializers.Serializer):
    pedido_id = serializers.IntegerField()

class ActualizarPedidoSerializer(serializers.Serializer):
    pedido_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=["increment", "decrement"])