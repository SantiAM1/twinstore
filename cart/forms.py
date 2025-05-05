from django import forms

class PedidoForm(forms.Form):
    TIPO_FACTURA_CHOICES = [
        ('A', 'IVA Responsable Inscripto'),
        ('B', 'Consumidor Final'),
    ]
    PROVINCIAS_CHOICES = [
        ('A', 'Ciudad Autónoma de Buenos Aires'),
        ('B', 'Buenos Aires'),
        ('C', 'Catamarca'),
        ('D', 'Chaco'),
        ('E', 'Chubut'),
        ('F', 'Córdoba'),
        ('G', 'Corrientes'),
        ('H', 'Entre Ríos'),
        ('I', 'Formosa'),
        ('J', 'Jujuy'),
        ('K', 'La Pampa'),
        ('L', 'La Rioja'),
        ('M', 'Mendoza'),
        ('N', 'Misiones'),
        ('O', 'Neuquén'),
        ('P', 'Río Negro'),
        ('Q', 'Salta'),
        ('R', 'San Juan'),
        ('S', 'San Luis'),
        ('T', 'Santa Cruz'),
        ('U', 'Santa Fe'),
        ('V', 'Santiago del Estero'),
        ('W', 'Tierra del Fuego'),
        ('X', 'Tucumán'),
    ]

    tipo_factura = forms.ChoiceField(choices=TIPO_FACTURA_CHOICES, required=True)
    dni_cuit = forms.CharField(max_length=255, required=False)
    razon_social = forms.CharField(max_length=255, required=False)
    nombre = forms.CharField(max_length=255, required=True)
    apellido = forms.CharField(max_length=255, required=True)
    calle = forms.CharField(max_length=255, required=True, label="Dirección de la calle")
    calle_detail = forms.CharField(max_length=255, required=False, label="Apartamento / Piso / Detalle")
    ciudad = forms.CharField(max_length=255, required=True, label="Localidad / Ciudad")
    provincia = forms.ChoiceField(choices=PROVINCIAS_CHOICES, required=True)
    codigo_postal = forms.CharField(max_length=10, required=True)
    email = forms.EmailField(required=True)
    telefono = forms.CharField(max_length=20, required=False)
