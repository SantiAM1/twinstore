from django.contrib import admin
from .models import PerfilUsuario, DatosFacturacion

# Register your models here.

admin.site.register(PerfilUsuario)
admin.site.register(DatosFacturacion)