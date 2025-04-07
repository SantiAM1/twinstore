from django import forms
from django.contrib.auth.models import User
import uuid

from django import forms

class UsuarioForm(forms.Form):
    TIPO_FACTURA_CHOICES = [
        ('A', 'IVA Responsable Inscripto'),
        ('B', 'Consumidor Final'),
        ('C', 'Monotributista'),
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
    INPUT_ATTRS = forms.TextInput(attrs={'class': 'form-input bloqueable font-roboto position-absolute width-100 height-100 border-none','autocomplete':'off','placeholder':' '})

    tipo_factura = forms.ChoiceField(
        choices=TIPO_FACTURA_CHOICES,
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
        label='Razon Social *',
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
    cuidad = forms.CharField(max_length=255, required=True, label="Localidad / Ciudad *",
        widget=INPUT_ATTRS
        )
    provincia = forms.ChoiceField(choices=PROVINCIAS_CHOICES, required=True,
        widget=SELECT_ATTRS
        )
    codigo_postal = forms.CharField(max_length=10, required=True, label="Codigo Postal *",
        widget=INPUT_ATTRS
        )
    email = forms.EmailField(required=True, label="Email *",
        widget=forms.EmailInput(attrs={'class': 'form-input bloqueable font-roboto position-absolute width-100 height-100 border-none','autocomplete':'off','placeholder':' '})
        )
    telefono = forms.CharField(max_length=20, required=False, label="Telefono",
        widget=INPUT_ATTRS
        )
    guardar_datos = forms.BooleanField(
        required=False,
        label="Recordar mis datos para futuras compras",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    recibir_estado_pedido = forms.BooleanField(
        required=False,
        label='Recibir mails sobre el estado del pedido',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class BuscarPedidoForm(forms.Form):
    token = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Código de búsqueda...',
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
    email = forms.EmailField(required=True,label="Email",widget=forms.EmailInput(attrs={
        'placeholder':'Email',
        'class':'user-form-control'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Contraseña',
        'class': 'user-form-control'
    }))

class RegistrarForm(forms.Form):
    email = forms.EmailField(required=True,label="Email",widget=forms.EmailInput(attrs={
        'placeholder':'Email',
        'class':'user-form-control'
    }))

    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Contraseña',
        'class': 'user-form-control'
    }))
    password_repeat = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Repetir contraseña',
        'class': 'user-form-control'
    }))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe un usuario registrado con este email.')
        return email

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
