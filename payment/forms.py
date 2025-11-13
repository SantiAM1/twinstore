from django import forms
from .models import EstadoPedido

class EstadoPedidoForm(forms.ModelForm):
    class Meta:
        model = EstadoPedido
        fields = ['estado', 'comentario']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['estado'].widget = forms.HiddenInput()
            self.fields['comentario'].widget = forms.HiddenInput()