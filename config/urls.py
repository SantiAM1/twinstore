from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from core.views import pagina_mantenimiento

urlpatterns = [
    path('panel-admin-twinstore/', admin.site.urls),
    path('',include('core.urls')),
    path('productos/',include('products.urls')),
    path('carro/',include('cart.urls')),
    path('usuario/',include('users.urls')),
    path('payment/',include('payment.urls')),
    path('mantenimiento/',pagina_mantenimiento,name="pagina_mantenimiento"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
