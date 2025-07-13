from rest_framework import serializers

class RecibirMailSerializer(serializers.Serializer):
    id = serializers.CharField()
