from django.db import models

from core.utils import get_configuracion_tienda
from django.db.models import Value,Q , Count, Prefetch, Sum
from django.db.models.functions import Coalesce
from .types import GridContext

class ProductQuerySet(models.QuerySet):

    def de_categoria(self, categoria):
        return self.filter(sub_categoria__in=categoria.subcategorias.all())

    def de_subcategoria(self, subcategoria):
        return self.filter(sub_categoria=subcategoria)

    def de_marca_slug(self, slug):
        return self.filter(marca__slug=slug)

    def de_busqueda(self, texto):
        return self.filter(
            Q(nombre__icontains=texto) |
            Q(slug__icontains=texto)
        )

    def precargado(self):
        from products.models import ColorProducto
        config = get_configuracion_tienda()
        modo_estricto = config.get('modo_stock') == 'estricto'

        qs = self.select_related("sub_categoria", "marca","evento")
        prefetchs_comunes = ["imagenes_producto", "colores__imagenes_color"]

        if modo_estricto:
            colores_con_stock = ColorProducto.objects.annotate(
                _stock_cache=Coalesce(
                    Sum(
                        'ingresos_stock__lotes__cantidad_disponible',
                        filter=Q(ingresos_stock__lotes__cantidad_disponible__gt=0)
                    ),
                    Value(0)
                )
            )

            return qs.annotate(
                _total_stock_cache=Coalesce(
                    Sum(
                        'ingresos_stock__lotes__cantidad_disponible',
                        filter=Q(ingresos_stock__lotes__cantidad_disponible__gt=0)
                    ),
                    Value(0)
                )
            ).prefetch_related(
                Prefetch('colores', queryset=colores_con_stock),
                *prefetchs_comunes
            )
        
        else:
            return qs.prefetch_related(
                'colores', 
                *prefetchs_comunes
            )

    def de_evento(self, evento):
        if not evento:
            return self

        return self.filter(evento=evento)
    
    def ordenar(self, request):
        orden = request.GET.get("ordenby", "")
        if orden == "price_lower":
            return self.order_by("precio_final"),'Menor precio'
        elif orden == "price_higher":
            return self.order_by("-precio_final"),'Mayor precio'
        elif orden == "date":
            return self.order_by("-id"),'Los últimos'

        return self, 'Ordenar por'


    def master_request(
        self,
        subcategoria_slug=None,
        categoria_slug=None,
        marca_slug=None,
        busqueda=None,
        evento=None,
        flag_filters=False,
        request=None
        ) -> GridContext:
        """
        Filtra productos, calcula marcas y atributos,
        y construye un contexto completo para el grid.

        Devuelve un diccionario listo para renderizar en la vista.
        """
        qs = self.precargado()

        categoria_obj = None
        subcategorias_qs = None
        marca_obj = None

        if subcategoria_slug:
            from products.models import SubCategoria
            subcat = SubCategoria.objects.filter(slug=subcategoria_slug).first()

            if subcat:
                qs = qs.de_subcategoria(subcat)

            title = subcat.nombre if subcat else "Productos"

        elif categoria_slug:
            from products.models import Categoria, SubCategoria
            categoria_obj = Categoria.objects.filter(slug=categoria_slug).first()

            if categoria_obj:
                subcats = SubCategoria.objects.filter(categoria=categoria_obj)
                qs = qs.filter(sub_categoria__in=subcats)
                subcategorias_qs = (
                    subcats.annotate(total=Count('productos', distinct=True))
                )

            title = categoria_obj.nombre if categoria_obj else "Productos"

        elif marca_slug:
            from products.models import Marca

            marca_obj = Marca.objects.filter(slug=marca_slug).first()
            qs = qs.de_marca_slug(marca_slug)

            title = marca_obj.nombre if marca_obj else "Productos"

        elif evento:
            qs = qs.de_evento(evento)
            title = evento.nombre_evento

        elif busqueda:
            qs = qs.de_busqueda(busqueda)
            title = "Resultados de búsqueda"

        else:
            title = "Productos"

        from products.utils import filters as filtros_utils

        if flag_filters and request:
            qs, atributos_unicos = filtros_utils(request, qs)
        else:
            atributos_unicos = {}

        from products.models import Marca

        marcas_qs = (
            Marca.objects
                .filter(producto__in=qs.values('id'))
                .annotate(total=Count('producto', distinct=True))
                .distinct()
        )

        if request:
            qs,filtro_label = qs.ordenar(request)

        return {
            "productos": qs,
            "title": title,
            "categoria": categoria_obj,
            "sub_categorias": subcategorias_qs,
            "sub_categoria_obj": subcat if subcategoria_slug else None,
            "marca": marca_obj,
            "evento": evento,
            "marcas": marcas_qs,
            "atributos": atributos_unicos,
            "filtro": filtro_label,
        }

class ProductoManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def master_request(self, **kwargs) -> GridContext:
        return self.get_queryset().master_request(**kwargs)

    def precargado(self):
        return self.get_queryset().precargado()

    def de_evento(self, evento):
        return self.get_queryset().de_evento(evento)

    def con_precio_final(self):
        return self.get_queryset().con_precio_final()

    def ordenar(self, request):
        return self.get_queryset().ordenar(request)