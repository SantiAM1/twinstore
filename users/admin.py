from django.contrib import admin
from .models import PerfilUsuario, DatosFacturacion,TokenUsers

# Register your models here.

admin.site.register(PerfilUsuario)
admin.site.register(TokenUsers)