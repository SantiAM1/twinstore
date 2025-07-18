from rest_framework import serializers

class HistorialIdSerializer(serializers.Serializer):
    id = serializers.CharField()
