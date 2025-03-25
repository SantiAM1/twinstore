from django import forms

class DatosEnvioForm(forms.Form):
    direccion_completa = forms.CharField(
        required=False,
        label="Dirección",
        widget=forms.TextInput(attrs={
            'id': 'autocomplete',
            'placeholder': 'Calle, Numero, Ciudad...',
            'class': 'users-facturacion-email',
            'autocomplete': 'off',
        })
    )
    calle = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'id': 'id_calle'}))
    altura = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'id': 'id_altura'}))
    ciudad = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'id': 'id_ciudad'}))
    provincia = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'id': 'id_provincia'}))
    codigo_postal = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'id': 'id_codigo_postal'}))
    latitud = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'id': 'id_latitud'}))
    longitud = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'id': 'id_longitud'}))