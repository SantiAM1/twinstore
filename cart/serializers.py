from rest_framework import serializers
import re

class AdicionalesCheckoutSerializer(serializers.Serializer):
    forma_de_pago = serializers.CharField()

    def validate_forma_de_pago(self, value):
        valid_choices = ["mercado_pago", "efectivo", "transferencia", "mixto","tarjeta"]
        if value not in valid_choices:
            raise serializers.ValidationError("Forma de pago inválida.")
        return value

class AgregarAlCarritoSerializer(serializers.Serializer):
    producto_id = serializers.CharField()
    color_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)

class EliminarPedidoSerializer(serializers.Serializer):
    pedido_id = serializers.CharField()

class ActualizarPedidoSerializer(serializers.Serializer):
    pedido_id = serializers.CharField()
    action = serializers.ChoiceField(choices=["mas", "menos"])

class CuponSerializer(serializers.Serializer):
    codigo = serializers.CharField(max_length=6)

class PagoMixtoSerializer(serializers.Serializer):
    monto = serializers.DecimalField(decimal_places=2,max_digits=10)

class ComprobanteSerializer(serializers.Serializer):
    comprobante = serializers.FileField(required=False, allow_null=True)

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

class CheckoutSerializer(serializers.Serializer):
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    email = serializers.EmailField()
    telefono = serializers.IntegerField()
    dni_cuit = serializers.CharField()
    razon_social = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    condicion_iva = serializers.CharField()
    direccion = serializers.CharField() 
    localidad = serializers.CharField()
    codigo_postal = serializers.CharField()
    provincia = serializers.CharField()

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

    def validate_condicion_iva(self, value):
        valid_choices = ["A", "B", "C"]
        if value not in valid_choices:
            raise serializers.ValidationError("Condición de IVA inválida.")
        return value

    def validate_razon_social(self, value):
        if value and not re.match(r'^[\w\s\.,\-&áéíóúÁÉÍÓÚñÑ]+$', value):
            raise serializers.ValidationError("Razón social inválida.")
        return value.strip()

    def validate_dni_cuit(self, value):
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
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-]+$', value):
            raise serializers.ValidationError("Localidad inválida.")
        return value.strip()

    def validate_codigo_postal(self, value):
        if not re.match(r'^[A-Z]?\d{4}[A-Z]{0,3}$', value, re.IGNORECASE):
            raise serializers.ValidationError("Código postal inválido.")
        return value.upper()

    def validate_provincia(self, value):
        if not re.match(r'^[A-Z]$', value):
            raise serializers.ValidationError("Provincia inválida.")
        return value