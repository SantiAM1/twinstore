from django import forms
from .models import Marca

class FiltroProductoForm(forms.Form):
    marca = forms.CharField(widget=forms.HiddenInput(), required=False)
    conectividad = forms.CharField(widget=forms.HiddenInput(), required=False)
