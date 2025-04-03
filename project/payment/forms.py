from django import forms
from .models import ComprobanteTransferencia
from django.core.exceptions import ValidationError

MAX_FILE_SIZE_MB = 5

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
            if not file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
                raise ValidationError("❌ Solo se permiten archivos JPG, JPEG, PNG o PDF.")
            
            max_size = MAX_FILE_SIZE_MB * 1024 * 1024  # MB to bytes
            if file.size > max_size:
                raise ValidationError(f"❌ El archivo supera el límite de {MAX_FILE_SIZE_MB} MB.")
        return file
