from django import forms
from django.contrib.auth.models import User

TIPO_FACTURA_CHOICES = [
    ('A', 'IVA Responsable Inscripto'),
    ('B', 'Consumidor Final'),
    ('C', 'Monotributista'),
]

class FacturacionForm(forms.Form):
    tipo_factura = forms.ChoiceField(choices=TIPO_FACTURA_CHOICES, label="Tipo de Factura")
    razon_social = forms.CharField(required=False,max_length=255, label="Razón Social", widget=forms.TextInput(attrs={
        'placeholder': 'Razón Social',
        'class': 'users-facturacion-input',
    }))
    dni_cuit = forms.CharField(max_length=20, label="DNI o CUIT", widget=forms.TextInput(attrs={
        'placeholder': 'DNI/CUIT',
        'class': 'users-facturacion-input'
    }))
    email = forms.EmailField(required=False, label="Email", widget=forms.EmailInput(attrs={
        'placeholder': 'Email',
        'class': 'users-facturacion-email'
    }))

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
