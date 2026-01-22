from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Client, Domain
from unfold.admin import ModelAdmin

# Register your models here.
@admin.register(Client)
class ClientAdmin(TenantAdminMixin, ModelAdmin):
        list_display = ('name',)

@admin.register(Domain)
class DomainAdmin(TenantAdminMixin, ModelAdmin):
        list_display = ('domain', 'tenant', 'is_primary')