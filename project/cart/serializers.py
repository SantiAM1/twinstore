from rest_framework import serializers

class CalcularPedidoSerializer(serializers.Serializer):
    total_precio = serializers.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = serializers.CharField()
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    email = serializers.EmailField()
    dni_cuit = serializers.CharField()
    tipo_factura = serializers.CharField()
    calle = serializers.CharField()
    cuidad = serializers.CharField()
    codigo_postal = serializers.CharField()
