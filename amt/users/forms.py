from django import forms
from django.contrib.auth.models import User
from .models import PerfilUsuario

class RegistroForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Contraseña'}),
        required=True
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirmar Contraseña'}),
        label="Confirmar contraseña",
        required=True
    )

    class Meta:
        model = User
        fields = ["email"]  # Eliminamos username
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Correo electrónico'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email.lower()

    def clean_password_confirm(self):
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # Usa el email como username
        user.set_password(self.cleaned_data["password"])  # Encripta la contraseña
        user.is_active = False  # Desactiva la cuenta hasta que verifique su email
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Correo electrónico'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Contraseña'})
    )
    remember_me = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class PerfilForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ["nombre","apellidos","direccion", "telefono", "fecha_nacimiento", "razon_social", "cuit"]
        widgets = {
            "direccion": forms.TextInput(attrs={"class": "form-input", "placeholder": "Dirección"}),
            "telefono": forms.TextInput(attrs={"class": "form-input", "placeholder": "Teléfono"}),
            "fecha_nacimiento": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "razon_social": forms.TextInput(attrs={"class": "form-input", "placeholder": "Razón Social"}),
            "cuit": forms.TextInput(attrs={"class": "form-input", "placeholder": "CUIT"}),
        }