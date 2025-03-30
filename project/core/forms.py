# forms.py
from django import forms

class ExcelUploadForm(forms.Form):
    archivo = forms.FileField(label="Seleccioná el archivo Excel (.xlsx)")
