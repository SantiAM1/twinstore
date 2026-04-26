from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Cupon,MercadoPagoConfig,DatosBancarios

from unfold.admin import ModelAdmin

@admin.register(DatosBancarios)
class DatosBancariosAdmin(ModelAdmin):
    fields = ('banco','titular_cuenta','numero_cuenta','cbu','alias','imagen_banco')
    readonly_fields = ()

@admin.register(MercadoPagoConfig)
class MercadoPagoConfigAdmin(ModelAdmin):
    fields = ('access_token','public_key','webhook_key')
    readonly_fields = ()

@admin.register(Cupon)
class CuponAdmin(ModelAdmin):
    fields = ('codigo','descuento','creado')
    readonly_fields = ('codigo','creado')
