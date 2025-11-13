from django import forms
from django.contrib.auth.models import User
import uuid

from django import forms
import re

class UsuarioForm(forms.Form):
    CONDICION_IVA_CHOICES = [
        ('A', 'IVA Responsable Inscripto'),
        ('B', 'Consumidor Final'),
        ('C', 'Monotributista')
    ]
    PROVINCIAS_CHOICES = [
        ('A', 'Ciudad Autónoma de Buenos Aires'),
        ('B', 'Buenos Aires'),
        ('C', 'Catamarca'),
        ('D', 'Chaco'),
        ('E', 'Chubut'),
        ('F', 'Córdoba'),
        ('G', 'Corrientes'),
        ('H', 'Entre Ríos'),
        ('I', 'Formosa'),
        ('J', 'Jujuy'),
        ('K', 'La Pampa'),
        ('L', 'La Rioja'),
        ('M', 'Mendoza'),
        ('N', 'Misiones'),
        ('O', 'Neuquén'),
        ('P', 'Río Negro'),
        ('Q', 'Salta'),
        ('R', 'San Juan'),
        ('S', 'San Luis'),
        ('T', 'Santa Cruz'),
        ('U', 'Santa Fe'),
        ('V', 'Santiago del Estero'),
        ('W', 'Tierra del Fuego'),
        ('X', 'Tucumán'),
    ]
    SELECT_ATTRS = forms.Select(attrs={'class': 'users-select bloqueable'})
    INPUT_ATTRS = forms.TextInput(attrs={'class': 'form-input bloqueable font-roboto position-absolute width-100 height-100','autocomplete':'off','placeholder':' '})

    condicion_iva = forms.ChoiceField(
        choices=CONDICION_IVA_CHOICES,
        required=True,
        widget=SELECT_ATTRS
    )
    dni_cuit = forms.CharField(
        max_length=255,
        required=True,
        label='DNI *',
        widget=INPUT_ATTRS
        )
    razon_social = forms.CharField(
        max_length=255,
        required=False,
        label='Razón Social *',
        widget=INPUT_ATTRS
        )
    nombre = forms.CharField(
        max_length=255,
        required=True,
        label='Nombre *',
        widget=INPUT_ATTRS
        )
    apellido = forms.CharField(
        max_length=255,
        required=True,
        label='Apellidos *',
        widget=INPUT_ATTRS
        )
    calle = forms.CharField(max_length=255, required=True, label="Dirección de la calle *",
        widget=INPUT_ATTRS
        )
    calle_detail = forms.CharField(max_length=255, required=False, label="Apartamento / Piso / Detalle",
        widget=INPUT_ATTRS
        )
    ciudad = forms.CharField(max_length=255, required=True, label="Localidad / Ciudad *",
        widget=INPUT_ATTRS
        )
    provincia = forms.ChoiceField(choices=PROVINCIAS_CHOICES, required=True,
        widget=SELECT_ATTRS
        )
    codigo_postal = forms.CharField(max_length=10, required=True, label="Código Postal *",
        widget=INPUT_ATTRS
        )
    email = forms.EmailField(required=True, label="Email *",
        widget=forms.EmailInput(attrs={'class': 'form-input bloqueable font-roboto position-absolute width-100 height-100','autocomplete':'off','placeholder':' '})
        )
    telefono = forms.CharField(max_length=20, required=False, label="Teléfono",
        widget=INPUT_ATTRS
        )
    recibir_estado_pedido = forms.BooleanField(
        required=False,
        label='Recibir mails sobre el estado del pedido',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    preferencias_promociones = forms.BooleanField(
        required=False,
        label='Recibir mails promocionales',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_razon_social(self):
        value = self.cleaned_data['razon_social']
        if value and not re.match(r'^[\w\s\.,\-&áéíóúÁÉÍÓÚñÑ]+$', value):
            raise forms.ValidationError("Razón social inválida.")
        return value

    def clean_codigo_postal(self):
        value = self.cleaned_data['codigo_postal']
        if not re.match(r'^[A-Z]?\d{4}[A-Z]{0,3}$', value, re.IGNORECASE):
            raise forms.ValidationError("Código postal inválido.")
        return value.upper()

    def clean_calle(self):
        value = self.cleaned_data['calle']
        value = value.strip()

        match = re.match(r'^(.*?)(?:\s+(\d+))$', value)
        if not match:
            raise forms.ValidationError("Debe ingresar calle y número")

        calle_nombre = match.group(1).strip()
        calle_altura = match.group(2)

        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', calle_nombre):
            raise forms.ValidationError("Nombre de calle inválido. Solo letras y espacios.")

        if not calle_altura.isdigit() or int(calle_altura) <= 0:
            raise forms.ValidationError("Altura de calle inválida.")

        return value
    
    def clean_ciudad(self):
        value = self.cleaned_data['ciudad']
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-]+$', value):
            raise forms.ValidationError("Ciudad inválida.")
        return value
    
    def clean_nombre(self):
        value = self.cleaned_data['nombre']
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise forms.ValidationError("El nombre solo debe contener letras y espacios.")
        return value
    
    def clean_apellido(self):
        value = self.cleaned_data['apellido']
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', value):
            raise forms.ValidationError("El apellido solo debe contener letras y espacios.")
        return value

    def clean_dni_cuit(self):
        value = self.cleaned_data['dni_cuit']
        if not value.isdigit():
            raise forms.ValidationError("El DNI/CUIT debe contener solo números")
        if len(value) in [7, 8]:
            return value
        elif len(value) == 11 and self._validar_cuit(value):
            return value
        else:
            raise forms.ValidationError("DNI/CUIT Invalido")

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

class TerminosYCondiciones(forms.Form):
    aceptar = forms.BooleanField(
        required=True,
        error_messages={
            'required': 'Debés aceptar los Términos y Condiciones para continuar.'
        })

class EmailUsuarioRecuperacion(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
        'placeholder':'Ingresa tu email',
        'class':'user-form-control',
        'style':'min-width:300px'
    }))

class BuscarPedidoForm(forms.Form):
    token = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Código de seguimiento...',
            'class': 'user-form-control',
        })
    )

    def clean_token(self):
        token = self.cleaned_data['token']
        try:
            uuid.UUID(token, version=4)
        except ValueError:
            raise forms.ValidationError("El código ingresado no es válido.")
        return token

class LoginForm(forms.Form):
    login_email = forms.EmailField(required=True)
    login_password = forms.CharField(required=True)

class RegistrarForm(forms.Form):
    reg_nombre = forms.EmailField(required=True)
    reg_apellido = forms.EmailField(required=True)
    reg_telefono = forms.EmailField(required=True)
    reg_email = forms.EmailField(required=True)
    reg_password = forms.CharField(required=True)
    reg_password_repeat = forms.CharField(required=True)

    def clean_reg_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe un usuario registrado con este email.')
        return email

    def clean_reg_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        reg_password = cleaned_data.get("reg_password")
        reg_password_repeat = cleaned_data.get("reg_password_repeat")

        if reg_password and reg_password_repeat and reg_password != reg_password_repeat:
            self.add_error('password_repeat', "Las contraseñas no coinciden.")

class RestablecerContraseña(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Contraseña',
        'class': 'user-form-control'
    }))
    password_repeat = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Repetir contraseña',
        'class': 'user-form-control'
    }))

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_repeat = cleaned_data.get("password_repeat")

        if password and password_repeat and password != password_repeat:
            self.add_error('password_repeat', "Las contraseñas no coinciden.")