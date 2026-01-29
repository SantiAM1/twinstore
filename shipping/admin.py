from django.contrib import admin
from .models import ShippingConfig
from unfold.admin import ModelAdmin

# Register your models here.
@admin.register(ShippingConfig)
class ShippingConfigAdmin(ModelAdmin):
    ...