# forms.py
from django import forms

class ExcelUploadForm(forms.Form):
    archivo = forms.FileField(label="Seleccioná el archivo Excel (.xlsx)",required=False)

class DolarActualizar(forms.Form):
    dolar = forms.DecimalField(label="Valor del Dolar", max_digits=10, decimal_places=2, required=False)

    def clear_dolar(self):
        dolar = self.cleaned_data.get('dolar')
        if dolar is None or dolar <= 0:
            raise forms.ValidationError("El valor del dólar debe ser un número positivo.")
        return dolar