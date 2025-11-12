from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from core.views import pagina_mantenimiento
from .sitemaps import StaticViewSitemap,CategoriaSitemap,SubCategoriaSitemap,ProductoSitemap,MarcaSitemap
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps.views import sitemap as sitemap_view

sitemaps = {
    'static': StaticViewSitemap,
    'categorias': CategoriaSitemap,
    'subcategorias': SubCategoriaSitemap,
    'productos': ProductoSitemap,
    'marcas': MarcaSitemap,
}

def sitemap_view(request):
    response = sitemap(request, sitemaps=sitemaps)
    response["Content-Type"] = "application/xml"
    return response


urlpatterns = [
    path('panel-admin-twinstore/', admin.site.urls),
    path('',include('core.urls')),
    path('productos/',include('products.urls')),
    path('carro/',include('cart.urls')),
    path('usuario/',include('users.urls')),
    path('payment/',include('payment.urls')),
    path('mantenimiento/',pagina_mantenimiento,name="pagina_mantenimiento"),
    path("sitemap.xml", sitemap_view, name="django.contrib.sitemaps.views.sitemap"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]