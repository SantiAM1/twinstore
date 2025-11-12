from rest_framework import serializers

class ComprobanteSerializer(serializers.Serializer):
    comprobante = serializers.FileField()
    historial_id = serializers.CharField()

    def validate_comprobante(self, file):
        if not file:
            return file
        max_size = 5 * 1024 * 1024
        allowed_ext = ['pdf', 'jpg', 'jpeg', 'png']
        ext = file.name.split('.')[-1].lower()

        if ext not in allowed_ext:
            raise serializers.ValidationError("Formato de archivo no permitido.")
        if file.size > max_size:
            raise serializers.ValidationError("El archivo excede los 5 MB.")
        return file

class IntSigned(serializers.Serializer):
    numero_firmado = serializers.CharField()