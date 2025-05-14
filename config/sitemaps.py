from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from products.models import Categoria, SubCategoria, Producto

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return ['core:home', 'products:gaming','core:contacto','core:politicas-tecnico','core:politicas-privacidad','core:politicas-devolucion','core:politicas-envios','core:faq','core:terminos-condiciones','core:arrepentimiento','core:quienes_somos','core:servicio_tecnico']

    def location(self, item):
        return reverse(item)


class CategoriaSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Categoria.objects.all().order_by('id')

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.updated_at


class SubCategoriaSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return SubCategoria.objects.all().order_by('id')

    def location(self, obj):
        return obj.get_absolute_url()
    
    def lastmod(self, obj):
        return obj.updated_at


class ProductoSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Producto.objects.all().order_by('id')

    def location(self, obj):
        return obj.get_absolute_url()
    
    def lastmod(self, obj):
        return obj.updated_at