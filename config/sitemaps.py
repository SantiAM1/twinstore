from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from products.models import Categoria, SubCategoria, Producto

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return ['core:home', 'products:gaming']

    def location(self, item):
        return reverse(item)


class CategoriaSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Categoria.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()


class SubCategoriaSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return SubCategoria.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()


class ProductoSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Producto.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()