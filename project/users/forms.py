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

    tipo_factura = forms.ChoiceField(
        choices=TIPO_FACTURA_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'users-select'})
    )
    dni_cuit = forms.CharField(
        max_length=255,
        required=True,
        label='DNI *',
        widget=forms.TextInput(attrs={'class': 'form__input','autocomplete':'off','placeholder':' '})
        )
    razon_social = forms.CharField(
        max_length=255,
        required=False,
        label='Razon Social *',
        widget=forms.TextInput(attrs={'class': 'form__input','autocomplete':'off','placeholder':' '})
        )
    nombre = forms.CharField(
        max_length=255,
        required=True,
        label='Nombre *',
        widget=forms.TextInput(attrs={'class': 'form__input','autocomplete':'off','placeholder':' '})
        )
    apellido = forms.CharField(
        max_length=255,
        required=True,
        label='Apellidos *',
        widget=forms.TextInput(attrs={'class': 'form__input','autocomplete':'off','placeholder':' '})
        )
    calle = forms.CharField(max_length=255, required=True, label="Dirección de la calle *",
        widget=forms.TextInput(attrs={'class': 'form__input','autocomplete':'off','placeholder':' '})
        )
    calle_detail = forms.CharField(max_length=255, required=False, label="Apartamento / Piso / Detalle",
        widget=forms.TextInput(attrs={'class': 'form__input','autocomplete':'off','placeholder':' '})
        )
    cuidad = forms.CharField(max_length=255, required=True, label="Localidad / Ciudad *",
        widget=forms.TextInput(attrs={'class': 'form__input','autocomplete':'off','placeholder':' '})
        )
    provincia = forms.ChoiceField(choices=PROVINCIAS_CHOICES, required=True,
        widget=forms.Select(attrs={'class': 'users-select'}))
    codigo_postal = forms.CharField(max_length=10, required=True, label="Codigo Postal *",
        widget=forms.TextInput(attrs={'class': 'form__input','autocomplete':'off','placeholder':' '})
        )
    email = forms.EmailField(required=True, label="Email *",
        widget=forms.EmailInput(attrs={'class': 'form__input','autocomplete':'off','placeholder':' '})
        )
    telefono = forms.CharField(max_length=20, required=False, label="Telefono",
        widget=forms.TextInput(attrs={'class': 'form__input','autocomplete':'off','placeholder':' '})
        )

class PreferenciasUsuarios(forms.Form):
    recibir_promociones = forms.BooleanField(required=False,label='Quiero rebicir notificaciones sobre promociones')
    recibir_estado_pedido = forms.BooleanField(required=False,label='Quiero rebicir mails sobre el estado de mi pedido')

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
