from django import forms
from .models import EspecificacionTecnica,Producto,ImagenProducto
import json

class EspecificacionTecnicaForm(forms.ModelForm):
    class Meta:
        model = EspecificacionTecnica
        fields = '__all__'
        widgets = {
            'datos': forms.Textarea(attrs={'rows': 4, 'cols': 80, 'style': 'font-family: monospace;'})
        }

class EditarProducto(forms.ModelForm):
    class Meta:
        INPUT_ATTRS = {'class': 'form-input bloqueable font-roboto position-absolute width-100 height-100 border-none','autocomplete':'off','placeholder':' '}
        model = Producto
        fields = ['nombre', 'marca', 'sub_categoria', 'precio_dolar', 'descuento', 'portada','precio']
        widgets = {
            'marca': forms.Select(attrs={'class': 'users-select bloqueable'}),
            'sub_categoria': forms.Select(attrs={'class': 'users-select bloqueable'}),
            'precio_dolar': forms.NumberInput(attrs=INPUT_ATTRS),
            'descuento': forms.NumberInput(attrs=INPUT_ATTRS),
            'nombre': forms.TextInput(attrs=INPUT_ATTRS),
            'portada': forms.FileInput(attrs={'class': 'form-admin-control display-none'}),
            'precio': forms.NumberInput(attrs={'class': 'form-input bloqueable font-roboto position-absolute width-100 height-100 border-none', 'readonly': 'readonly'})
        }

class ImagenProductoForm(forms.ModelForm):
    class Meta:
        model = ImagenProducto
        fields = ['imagen']
        widgets = {
            'imagen': forms.FileInput(attrs={'class': 'form-admin-control display-none'}),
        }