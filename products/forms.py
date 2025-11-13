from django import forms
from .models import EspecificacionTecnica,Producto,ImagenProducto,ColorProducto

class EspecificacionTecnicaForm(forms.ModelForm):
    class Meta:
        model = EspecificacionTecnica
        fields = '__all__'
        widgets = {
            'datos': forms.Textarea(attrs={'rows': 4, 'cols': 80, 'style': 'font-family: monospace;'})
        }

class EditarProducto(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'marca', 'sub_categoria', 'precio_dolar','descripcion_seo', 'descuento','precio','inhabilitar']
        widgets = {
            'marca': forms.Select(attrs={'class': 'users-select bloqueable'}),
            'sub_categoria': forms.Select(attrs={'class': 'users-select bloqueable'}),
            'precio_dolar': forms.NumberInput(),
            'descripcion_seo': forms.Textarea(attrs={'style': 'width: 100%;border: 1px solid #bdbdbd;border-radius: 8px;padding: 0.5rem;font-size: 0.9rem;resize: vertical;min-height: 80px;max-height: 150px;'}),
            'descuento': forms.NumberInput(),
            'nombre': forms.TextInput(),
            'precio': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'inhabilitar':forms.CheckboxInput()
        }

class ImagenProductoForm(forms.ModelForm):
    class Meta:
        model = ImagenProducto
        fields = ['imagen']
        widgets = {
            'imagen': forms.FileInput(attrs={'class': 'form-admin-control display-none'}),
        }
        
class ImagenProductoForm(forms.ModelForm):
    class Meta:
        model = ImagenProducto
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        producto = None

        if self.initial:
            producto = self.initial.get('producto')

        if not producto and getattr(self.instance, 'producto', None):
            producto = self.instance.producto

        if producto:
            self.fields['color'].queryset = ColorProducto.objects.filter(producto=producto)
        else:
            self.fields['color'].queryset = ColorProducto.objects.none()
