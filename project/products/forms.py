from django import forms
from .models import EspecificacionTecnica,Producto,ImagenProducto
import json
from django.forms import modelformset_factory

class EspecificacionTecnicaForm(forms.ModelForm):
    class Meta:
        model = EspecificacionTecnica
        fields = '__all__'
        widgets = {
            'datos': forms.Textarea(attrs={'rows': 4, 'cols': 80, 'style': 'font-family: monospace;'})
        }

    def clean_datos(self):
        datos = self.cleaned_data.get('datos')

        if datos in [None, ""]:
            return {}

        if isinstance(datos, str):
            try:
                return json.loads(datos)
            except json.JSONDecodeError:
                raise forms.ValidationError("El contenido no es un JSON válido. Usá formato correcto como: {\"clave\": \"valor\"}")

        return datos

class EditarProducto(forms.ModelForm):
    class Meta:
        INPUT_ATTRS = {'class': 'form-input bloqueable font-roboto position-absolute width-100 height-100 border-none','autocomplete':'off','placeholder':' '}
        model = Producto
        fields = ['nombre', 'marca', 'sub_categoria', 'precio', 'descuento', 'portada']
        widgets = {
            'marca': forms.Select(attrs={'class': 'users-select bloqueable'}),
            'sub_categoria': forms.Select(attrs={'class': 'users-select bloqueable'}),
            'precio': forms.NumberInput(attrs=INPUT_ATTRS),
            'descuento': forms.NumberInput(attrs=INPUT_ATTRS),
            'nombre': forms.TextInput(attrs=INPUT_ATTRS),
            'portada': forms.FileInput(attrs=INPUT_ATTRS),
        }

class ImagenProductoForm(forms.ModelForm):
    class Meta:
        model = ImagenProducto
        fields = ['imagen']
        widgets = {
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }

ImagenProductoFormSet = modelformset_factory(
    ImagenProducto,
    form=ImagenProductoForm,
    extra=3,
    can_delete=True
)