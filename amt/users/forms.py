from django import forms

class FacturacionForm(forms.Form):
    TIPO_FACTURA_CHOICES = [
        ('B', 'Comsumidor Final'),
        ('A', 'IVA Responsable Inscripto'),
        ('C', 'Monotributista'),
    ]

    tipo_factura = forms.ChoiceField(
        choices=TIPO_FACTURA_CHOICES,
        label='Tipo de Factura',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    razon_social = forms.CharField(
        max_length=255,
        required=False,
        label='Razón Social',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    dni_cuit = forms.CharField(
        max_length=20,
        label='DNI o CUIT',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
