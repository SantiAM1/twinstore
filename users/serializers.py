from rest_framework import serializers

class RecibirMailSerializer(serializers.Serializer):
    token = serializers.UUIDField()
