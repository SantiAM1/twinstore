from rest_framework import serializers
import re
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User

class ReseñaSerializer(serializers.Serializer):
    rating = serializers.IntegerField()
    review = serializers.CharField(max_length=250, allow_blank=True, required=False)
    token = serializers.UUIDField()

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La calificación debe estar entre 1 y 5.")
        return value

class PedidoSerializer(serializers.Serializer):
    order_id = serializers.CharField()

    def validate_order_id(self, value):
        if not len(value) == 11:
            raise serializers.ValidationError("ID de pedido inválido.")
        return value

class RecuperarCuentaSerializer(serializers.Serializer):
    email = serializers.EmailField()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class TokenSerializer(serializers.Serializer):
    codigo = serializers.CharField()

class NuevaContraseñaSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    password_repeat = serializers.CharField(write_only=True)

    def validate(self, data):
        password = data.get("password")
        password_repeat = data.get("password_repeat")

        if password != password_repeat:
            raise serializers.ValidationError({"password_repeat": "Las contraseñas no coinciden."})
        
        try:
            validate_password(password)
        except Exception as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return data

class RegisterSerializer(serializers.Serializer):
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    email = serializers.EmailField()
    telefono = serializers.IntegerField()
    password = serializers.CharField(write_only=True)
    password_repeat = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe un usuario registrado con este email.")
        return value

    def validate_nombre(self, value):
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError("El nombre solo debe contener letras y espacios.")
        return value
    
    def validate_telefono(self, value):
        value_str = str(value)
        if not re.match(r'^\d{8,15}$', value_str):
            raise serializers.ValidationError("El teléfono debe contener solo números y tener entre 8 y 15 dígitos.")
        return value_str

    def validate_apellido(self, value):
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError("El apellido solo debe contener letras y espacios.")
        return value

    def validate(self, data):
        password = data.get("password")
        password_repeat = data.get("password_repeat")

        if password != password_repeat:
            raise serializers.ValidationError({"password_repeat": "Las contraseñas no coinciden."})
        
        try:
            validate_password(password)
        except Exception as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return data

class MiCuentaSerializer(serializers.Serializer):
    dni_cuit = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    razon_social = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    condicion_iva = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    direccion = serializers.CharField(required=False, allow_blank=True, allow_null=True) 
    localidad = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    codigo_postal = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    provincia = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_condicion_iva(self, value):
        if not value:
            return value
        valid_choices = ["A", "B", "C"]
        if value not in valid_choices:
            raise serializers.ValidationError("Condición de IVA inválida.")
        return value

    def validate_razon_social(self, value):
        if not value:
            return value
        if value and not re.match(r'^[\w\s\.,\-&áéíóúÁÉÍÓÚñÑ]+$', value):
            raise serializers.ValidationError("Razón social inválida.")
        return value.strip()

    def validate_dni_cuit(self, value):
        if not value:
            return value
        if not value.isdigit():
            raise serializers.ValidationError("El DNI/CUIT debe contener solo números.")
        if len(value) in [7, 8]:
            return value
        elif len(value) == 11 and self._validar_cuit(value):
            return value
        raise serializers.ValidationError("DNI/CUIT inválido.")

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

    def validate_direccion(self, value):
        if not value:
            return value
        value = value.strip()

        match = re.match(r'^(.+?)\s+(\d+)(.*)$', value)
        if not match:
            raise serializers.ValidationError(
                "Debe ingresar calle y altura (por ejemplo: 'Av. Cabildo 1111 Piso 5B')."
            )

        nombre_calle = match.group(1).strip()
        altura = match.group(2).strip()
        resto = match.group(3).strip()

        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\.\']+$', nombre_calle):
            raise serializers.ValidationError(
                "Nombre de calle inválido. Solo letras, espacios y puntos."
            )

        if not altura.isdigit():
            raise serializers.ValidationError("Altura de calle inválida.")

        if resto and not re.match(r'^[a-zA-Z0-9\sº°\-\./]+$', resto):
            raise serializers.ValidationError(
                "Formato inválido en la dirección (revise piso/departamento)."
            )
        return value

    def validate_localidad(self, value):
        if not value:
            return value
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-]+$', value):
            raise serializers.ValidationError("Localidad inválida.")
        return value.strip()

    def validate_codigo_postal(self, value):
        if not value:
            return value
        if not re.match(r'^[A-Z]?\d{4}[A-Z]{0,3}$', value, re.IGNORECASE):
            raise serializers.ValidationError("Código postal inválido.")
        return value.upper()

    def validate_provincia(self, value):
        if not value:
            return value
        if not re.match(r'^[A-Z]$', value):
            raise serializers.ValidationError("Provincia inválida.")
        return value
