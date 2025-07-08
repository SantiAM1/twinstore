from rest_framework import serializers
import re
class CalcularPedidoSerializer(serializers.Serializer):
    metodo_pago = serializers.CharField()
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    email = serializers.EmailField()
    dni_cuit = serializers.CharField()
    razon_social = serializers.CharField(required=False,allow_blank=True)
    telefono = serializers.CharField(required=False,allow_blank=True)
    condicion_iva = serializers.CharField()
    calle = serializers.CharField()
    ciudad = serializers.CharField()
    codigo_postal = serializers.CharField()
    recibir_mail = serializers.BooleanField()

    def validate_razon_social(self, value):
        if value and not re.match(r'^[\w\s\.,\-&áéíóúÁÉÍÓÚñÑ]+$', value):
            raise serializers.ValidationError("Razón social inválida.")
        return value

    def validate_codigo_postal(self, value):
        if not re.match(r'^[A-Z]?\d{4}[A-Z]{0,3}$', value, re.IGNORECASE):
            raise serializers.ValidationError("Código postal inválido.")
        return value.upper()

    def validate_calle(self, value):
        value = value.strip()

        match = re.match(r'^(.*?)(?:\s+(\d+))$', value)
        if not match:
            raise serializers.ValidationError("Debe ingresar calle y número")

        calle_nombre = match.group(1).strip()
        calle_altura = match.group(2)

        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', calle_nombre):
            raise serializers.ValidationError("Nombre de calle inválido. Solo letras y espacios.")

        if not calle_altura.isdigit() or int(calle_altura) <= 0:
            raise serializers.ValidationError("Altura de calle inválida.")

        return value

    def validate_ciudad(self, value):
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-]+$', value):
            raise serializers.ValidationError("Ciudad inválida.")
        return value

    def validate_nombre(self, value):
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError("El nombre solo debe contener letras y espacios.")
        return value

    def validate_apellido(self, value):
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError("El apellido solo debe contener letras y espacios.")
        return value

    def validate_dni_cuit(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("El DNI/CUIT debe contener solo números")
        if len(value) in [7, 8]:
            return value
        elif len(value) == 11 and self._validar_cuit(value):
            return value
        else:
            raise serializers.ValidationError("DNI/CUIT Invalido")

    def _validar_cuit(self, cuit):
        mult = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        try:
            total = sum(int(cuit[i]) * mult[i] for i in range(10))
            verificador = 11 - (total % 11)
            if verificador == 11:
                verificador = 0
            elif verificador == 10:
                verificador = 9
            return verificador == int(cuit[-1])
        except (ValueError, IndexError):
            return False

class AgregarAlCarritoSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField()
    color = serializers.IntegerField(required=False, allow_null=True)

class EliminarPedidoSerializer(serializers.Serializer):
    pedido_id = serializers.CharField()

class ActualizarPedidoSerializer(serializers.Serializer):
    pedido_id = serializers.CharField()
    action = serializers.ChoiceField(choices=["increment", "decrement"])

class CuponSerializer(serializers.Serializer):
    codigo = serializers.CharField(max_length=10)

class PagoMixtoSerializer(serializers.Serializer):
    numero = serializers.DecimalField(decimal_places=2,max_digits=10)