from django import forms
from .models import ComprobanteTransferencia,EstadoPedido
from django.core.exceptions import ValidationError
import magic

MAX_FILE_SIZE_MB = 2

class ComprobanteForm(forms.ModelForm):
    class Meta:
        model = ComprobanteTransferencia
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={
                'accept': '.jpg, .jpeg, .png, .pdf',
                'class': 'input-subir-comprobante'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # ✅ Verificá extensión
            ext_permitidas = ['.jpg', '.jpeg', '.png', '.pdf']
            if not file.name.lower().endswith(tuple(ext_permitidas)):
                raise ValidationError("❌ Solo se permiten archivos JPG, JPEG, PNG o PDF.")
            
            # ✅ Verificá tipo real de archivo
            file_type = magic.from_buffer(file.read(2048), mime=True)
            file.seek(0)  # Volvés al inicio del archivo para evitar romper el guardado

            if file_type not in ['image/jpeg', 'image/png', 'application/pdf']:
                raise ValidationError(f"❌ Tipo de archivo inválido: {file_type}")

            # ✅ Validá tamaño
            max_size = MAX_FILE_SIZE_MB * 1024 * 1024
            if file.size > max_size:
                raise ValidationError(f"❌ El archivo supera el límite de {MAX_FILE_SIZE_MB} MB.")

        return file

class EstadoPedidoForm(forms.ModelForm):
    class Meta:
        model = EstadoPedido
        fields = ['estado', 'comentario']  # Campos editables

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si es una instancia ya guardada, ocultamos los campos
        if self.instance and self.instance.pk:
            self.fields['estado'].widget = forms.HiddenInput()
            self.fields['comentario'].widget = forms.HiddenInput()