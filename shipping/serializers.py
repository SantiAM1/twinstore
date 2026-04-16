from rest_framework import serializers
import re

class EnvioSerializer(serializers.Serializer):
    localidad_cotiza = serializers.CharField()
    codigo_postal_cotiza = serializers.IntegerField()
    provincia_cotiza = serializers.CharField()

class ObtenerSucursalesSerializer(serializers.Serializer):
    service_code = serializers.CharField()
    carrier_name = serializers.CharField()

class ValidarEnvioSerializer(serializers.Serializer):
    metodo_envio = serializers.CharField() 
    calle_domicilio = serializers.CharField(required=False, allow_blank=True)
    altura_domicilio = serializers.CharField(required=False, allow_blank=True)
    referencias_domicilio = serializers.CharField(required=False, allow_blank=True)
    nombre_reciver = serializers.CharField()
    dni_reciver = serializers.CharField()
    email_reciver = serializers.EmailField()
    phone_reciver = serializers.IntegerField()
    point_id = serializers.CharField(required=False, allow_blank=True)
    id = serializers.CharField()

    def validate_nombre_reciver(self, value):
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise serializers.ValidationError("El nombre solo debe contener letras y espacios.")
        return value
    
    def validate_phone_reciver(self, value):
        value_str = str(value)
        if not re.match(r'^\d{8,15}$', value_str):
            raise serializers.ValidationError("El teléfono debe contener solo números y tener entre 8 y 15 dígitos.")
        return value_str

    def validate_dni_reciver(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("El DNI/CUIT debe contener solo números.")
        if len(value) in [7, 8]:
            return value
        raise serializers.ValidationError("DNI/CUIT inválido.")

    def validate_calle_domicilio(self, value):
        if not value:
            return value
        if not value.replace(' ', '').isalpha():
            raise serializers.ValidationError("La calle solo debe contener letras y espacios.")
        return value

    def validate_altura_domicilio(self, value):
        if not value:
            return value
        if not value.isdigit():
            raise serializers.ValidationError("La altura debe contener solo números.")
        return value

    def validate_metodo_envio(self, value):
        allowed_methods = ['standard_delivery', 'pickup_point']
        if value not in allowed_methods:
            raise serializers.ValidationError(
                f"El método de envío debe ser uno de los siguientes: {', '.join(allowed_methods)}."
            )
        return value

    def validate(self, data):
        metodo = data.get('metodo_envio')

        if metodo == 'standard_delivery':
            errores = {}
            if not data.get('calle_domicilio'):
                errores['calle_domicilio'] = "Este campo es obligatorio para envíos a domicilio."
            if not data.get('altura_domicilio'):
                errores['altura_domicilio'] = "Este campo es obligatorio para envíos a domicilio."
            
            if errores:
                raise serializers.ValidationError(errores)
        
        elif metodo == 'pickup_point':
            data.pop('calle_domicilio', None)
            data.pop('altura_domicilio', None)
            data.pop('referencias_domicilio', None)

            if not data.get('point_id'):
                raise serializers.ValidationError({
                    "point_id": "Debes seleccionar un punto de retiro."
                })

        return data