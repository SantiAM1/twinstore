from rest_framework import serializers

class IntSigned(serializers.Serializer):
    numero_firmado = serializers.CharField()