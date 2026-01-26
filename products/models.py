from django.db import models
from django.db.models import Sum
from core.utils import get_configuracion_tienda
from django.utils.text import slugify
from django.urls import reverse
from django.templatetags.static import static
import uuid
from decimal import Decimal
from products.utils_debug import debug_queries
from django.conf import settings
from .managers import ProductQuerySet
from django.core.exceptions import ValidationError

class Marca(models.Model):
    nombre = models.CharField(max_length=30)
    slug = models.SlugField(max_length=50, blank=True,unique=True)

    def get_absolute_url(self):
        base_url = reverse('products:grid')
        print(base_url)
        return f"{base_url}?marca={self.slug}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion_seo = models.CharField(
    max_length=160,
    blank=True,
    help_text="Descripción corta para SEO (aparece en Google). Máximo 160 caracteres."
    )
    slug = models.SlugField(max_length=50, blank=True,unique=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('products:slug_dispatcher',args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class SubCategoria(models.Model):
    nombre = models.CharField(max_length=30)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='subcategorias')
    descripcion_seo = models.CharField(max_length=160,blank=True,help_text="Descripción corta para SEO (aparece en Google). Máximo 160 caracteres.")
    slug = models.SlugField(max_length=50, blank=True,unique=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('products:subcategoria_view',args=[self.categoria.slug,self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.nombre

class Atributo(models.Model):
    """
        Ejemplo: Almacenamiento 256 GB
        nombre: Almacenamiento
        valor: 256 GB
    """
    nombre = models.CharField(max_length=50,help_text="Ej: Almacemaniento, Consumo electrico")
    valor = models.CharField(max_length=50,help_text="Ej: 256 GB, 200W")

    class Meta:
        unique_together = ('nombre', 'valor')
        ordering = ['nombre','valor']

    def __str__(self):
        return f"{self.nombre}: {self.valor}"

class Etiquetas(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=50,unique=True)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    sub_categoria = models.ForeignKey(SubCategoria, on_delete=models.CASCADE, related_name='productos',null=True,blank=True)
    precio_divisa = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    precio_evento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precio_final = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    descuento = models.IntegerField(default=0)
    sku = models.CharField(max_length=20, unique=True, blank=True, null=True,editable=False)
    descripcion_seo = models.CharField(max_length=160,blank=True,help_text="Descripción corta para SEO (aparece en Google). Máximo 160 caracteres.")
    inhabilitar = models.BooleanField(default=False)
    slug = models.SlugField(max_length=100, blank=True,unique=True)
    updated_at = models.DateTimeField(auto_now=True)
    etiquetas = models.ManyToManyField(Etiquetas, blank=True, related_name='productos')
    atributos = models.ManyToManyField(Atributo,blank=True,related_name='productos')
    evento = models.ForeignKey('core.EventosPromociones',on_delete=models.SET_NULL,blank=True,null=True)
    objects: ProductQuerySet = ProductQuerySet.as_manager()

    def get_absolute_url(self):
        return reverse('products:slug_dispatcher',args=[self.slug])

    def save(self, *args, **kwargs):
        if self.pk:
            original = Producto.objects.filter(pk=self.pk).first()
            if original and original.nombre != self.nombre:
                self.slug = None

        self.generar_slug()
        self.generar_sku()
        self.calcular_precio_sin_evento()
        super().save(*args, **kwargs)

        self.calcular_precio_con_eventos()
        super().save(update_fields=['precio_evento','precio_final'])

    def generar_slug(self):
        if not self.slug:
            base_slug = slugify(self.nombre)
            slug = base_slug
            i = 1
            while Producto.objects.exclude(id=self.id).filter(slug=slug).exists():
                slug = f"{base_slug}-{i}"
                i += 1
            self.slug = slug

    def generar_sku(self):
        if not self.sku:
            prod_marca = slugify(self.marca.nombre).upper()[:3]
            prod_subcat = slugify(self.sub_categoria.nombre).upper()[:3] if self.sub_categoria else "GEN"
            unique_id = uuid.uuid4().hex[:4].upper()
            self.sku = f"{prod_marca}-{prod_subcat}-{unique_id}"
            while Producto.objects.exclude(id=self.id).filter(sku=self.sku).exists():
                unique_id = uuid.uuid4().hex[:4].upper()
                self.sku = f"{prod_marca}-{prod_subcat}-{unique_id}"

    def calcular_precio_sin_evento(self):
        from core.models import Tienda
        config = get_configuracion_tienda()
        if config['divisa'] == Tienda.Divisas.USD:
            self.precio_base = round(self.precio_divisa * config['valor_dolar'], 2)
        else:
            self.precio_base = self.precio_divisa
        
        if self.descuento > 0:
            descuento_decimal = Decimal(self.descuento) / Decimal('100')
            self.precio = round(self.precio_base * (1 - descuento_decimal), 2)
        else:
            self.precio = self.precio_base
    
    def calcular_precio_con_eventos(self):
        evento = self.evento

        if evento:
            if evento.descuento_porcentaje > 0:
                d = Decimal(evento.descuento_porcentaje) / Decimal('100')
                self.precio_evento = round(self.precio_base * (1 - d), 2)

            elif evento.descuento_fijo > 0:
                self.precio_evento = round(self.precio_base - evento.descuento_fijo, 2)
        else:
            self.precio_evento = None

        self.precio_final = min(
            [p for p in [self.precio, self.precio_evento] if p is not None]
        )
    
    def banner(self):
        """
        Texto a mostrar en la banderita de la card:
        * Si hay evento → se muestra el descuento del evento.
        * Si no hay evento pero hay descuento propio → se muestra el del producto.
        * Si no hay nada → devuelve None.
        """
        if not self.evento_id:
            if getattr(self, 'descuento', 0) and self.descuento > 0:
                return f"-{self.descuento}%"
            return None

        evento = self.evento
        if evento and evento.esta_activo:
            if evento.descuento_porcentaje:
                return f"-{int(evento.descuento_porcentaje)}%"
            if evento.descuento_fijo:
                base = self.precio_base
                descuento = (evento.descuento_fijo / base) * Decimal("100")
                return f"-{int(descuento)}%"
        
        if getattr(self,'descuento',0) and self.descuento > 0:
            return f"-{self.descuento}%"
        return None

    def obtener_stock_dict(self):
        """
        Devuelve {sku: stock} si tiene variantes, o {'total': stock} si no.
        Optimizado para usar datos precargados si existen.
        """
        stock_dict = {}
        variantes = self.variantes.all()
        if len(variantes) > 0:
            for variante in variantes:
                if hasattr(variante, '_stock_cache'):
                    stock_dict[variante.sku] = variante._stock_cache
                else:
                    stock = (LoteStock.objects.filter(
                        ingreso__variante=variante,
                        cantidad_disponible__gt=0
                    ).aggregate(t=Sum("cantidad_disponible"))["t"] or 0)
                    stock_dict[variante.sku] = stock
                
            return stock_dict
        
        else:
            if hasattr(self, '_total_stock_cache'):
                return {'total': self._total_stock_cache}

            total_stock = (LoteStock.objects.filter(
                ingreso__producto=self,
                cantidad_disponible__gt=0
            ).aggregate(t=Sum("cantidad_disponible"))["t"] or 0)
            
            stock_dict['total'] = total_stock
            return stock_dict

    def obtener_stock(self) -> int:
        return (
            LoteStock.objects.filter(
                ingreso__producto=self,
                cantidad_disponible__gt=0
            ).aggregate(total=Sum("cantidad_disponible"))["total"] or 0
        )

    def get_portada_200(self):
        """
        Devuelve la URL de la imagen principal del producto en tamaño 200px,
        o una imagen por defecto si no hay imágenes asociadas.
        """
        imagenes = self.imagenes_producto.all()
        imagen = imagenes[0] if imagenes else None
        if imagen:
            return imagen.imagen_200.url if imagen.imagen_200 else imagen.imagen.url
        return static('img/prod_default.webp')

    def get_portada_600(self):
        """
        Devuelve la URL de la imagen principal del producto en tamaño 600px,
        o una imagen por defecto si no hay imágenes asociadas.
        """
        imagenes = self.imagenes_producto.all()
        imagen = imagenes[0] if imagenes else None
        if imagen:
            return imagen.imagen.url if imagen.imagen else None
        return static('img/prod_default.webp')

    def get_imagen_carro(self):
        """Producto:"""
        imagenes = list(self.imagenes_producto.all())
        if imagenes:
            imagen = imagenes[0]
            return imagen.imagen_200.url if imagen.imagen_200 else imagen.imagen.url

        return static('img/prod_default.webp')

    def obtener_variantes(self):
        from collections import defaultdict
        raw_data = self.variantes.all().values(
                    'sku', 
                    'valores__tipo__nombre',
                    'valores__valor',
                    'valores__metadatos'
                )
        
        agrupado = defaultdict(dict)
        
        for item in raw_data:
            tipo = item['valores__tipo__nombre']
            valor = item['valores__valor']
            sku = item['sku']
            
            if not tipo or not valor: continue

            if valor not in agrupado[tipo]:
                agrupado[tipo][valor] = {
                    'valor': valor,
                    'metadatos': item['valores__metadatos'],
                    'skus': []
                }
            
            agrupado[tipo][valor]['skus'].append(sku)
        
        return {
            tipo: list(datos.values())
            for tipo, datos in agrupado.items()
        }

    def obtener_imagenes(self):
        """
        Retorna un diccionario con imágenes agrupadas por color.
        """
        data = {}
        todas_imagenes = list(self.imagenes_producto.all())
        variantes = list(self.variantes.all())

        if not variantes:
            data[self.sku] = [img for img in todas_imagenes]
            return data

        for variante in variantes:
            valores = list(variante.valores.all())
            
            color_variante = None
            for val in valores:
                if val.tipo.slug == "color":
                    color_variante= val
                    data[color_variante.valor] = []
                    break

            if color_variante:
                for img in todas_imagenes:
                    if img.variante_id == color_variante.id:
                        data[color_variante.valor].append(img)
            else:
                data['imagenes'] = todas_imagenes

        return data

    def __str__(self):
        return self.nombre

class TipoAtributo(models.Model):
    """Ej: Color, Talle, Material, Voltaje"""
    nombre = models.CharField(max_length=50,help_text="Ej: Color, Talle, Material, Voltaje")
    slug = models.SlugField(blank=True)

    def save(self, *args, **kwargs):
        self.generar_slug()
        return super().save(*args, **kwargs)

    def generar_slug(self):
        if self.slug:
            return
        self.slug = slugify(self.nombre)

    def __str__(self):
        return f"{self.nombre}"

class ValorAtributo(models.Model):
    """Ej: Rojo, XL, Plastico, 220v"""
    tipo = models.ForeignKey(TipoAtributo, on_delete=models.CASCADE,related_name='valores')
    valor = models.CharField(max_length=50,help_text="Ej: Blanco, XL, Plastico, 220v")
    metadatos = models.CharField(max_length=50,blank=True, null=True,help_text="Ej: #ffffff (Para utilizar el color blanco)")

    def __str__(self):
        return f"{self.tipo}: {self.valor}"

class Variante(models.Model):
    """La entidad física que tiene stock y precio"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='variantes')
    sku = models.CharField(max_length=100, unique=True, blank=True) 
    valores = models.ManyToManyField(ValorAtributo)

    def save(self, *args, **kwargs):
        self.generar_sku()
        return super().save(*args, **kwargs)
    
    def resumen(self):
        valores = self.valores.all()
        
        if not valores:
            return ""

        lista_resumen = [f"{v.tipo.nombre}: {v.valor}" for v in valores]
        return " | ".join(lista_resumen)

    def generar_sku(self):
        if self.sku:
            return
        if not self.producto.sku:
            self.producto.save()
        
        base_sku = self.producto.sku
        suffix = uuid.uuid4().hex[:4].upper()
        new_sku = f'{base_sku}-{suffix}'

        while Variante.objects.filter(sku=new_sku).exists():
            suffix = uuid.uuid4().hex[:4].upper()
            new_sku = f'{base_sku}-{suffix}'

        self.sku = new_sku

    def get_imagen_carro(self):
        """
        Variante:
        Retorna la imagen del producto para el carro de compras,
        """
        valores = list(self.valores.all())
        for valor in valores:
            if valor.tipo.slug == 'color':
                imgs = valor.imagenes_asociadas.all()
                if imgs:
                    img = imgs[0]
                    return img.imagen_200.url if img.imagen_200 else img.imagen.url
        
        return self.producto.get_imagen_carro()

    def obtener_stock(self):
        return (
            LoteStock.objects.filter(
                ingreso__variante=self,
                cantidad_disponible__gt=0
            ).aggregate(total=Sum("cantidad_disponible"))["total"] or 0
        )

    class Meta:
        verbose_name = "Variante"
        verbose_name_plural = "Variantes"
    
    def __str__(self):
        return self.resumen()
            
class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes_producto',  blank=True)
    variante = models.ForeignKey(
        ValorAtributo, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='imagenes_asociadas',
        help_text="Dejar vacío si la imagen es general. Seleccionar un valor (ej: Rojo) si la imagen es específica."
    )
    imagen = models.ImageField(upload_to='productos/imagenes/')
    imagen_200 = models.ImageField(upload_to='productos/imagenes/', null=True, blank=True,editable=False)

    class Meta:
        verbose_name = "Imagen"
        verbose_name_plural = "Imagenes"

class EspecificacionTecnica(models.Model):
    """
        Ejemplo: iPhone 13
        clave: Display
        valor: 11 plugadas dragon x
    """
    producto = models.ForeignKey(Producto, related_name='especificaciones', on_delete=models.CASCADE)
    clave = models.CharField(max_length=50,default="")
    valor = models.CharField(max_length=255,default="")

    class Meta:
        verbose_name = "Especificacion Técnica"
        verbose_name_plural = "Especificaciones Técnicas"
        ordering = ['clave']

    def __str__(self):
        return f"{self.producto} - {self.clave}"

class ReseñaProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='reseñas')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    comentario = models.TextField(max_length=250)
    calificacion = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.producto.nombre} - {self.usuario.first_name if self.usuario else 'Anonimo'} ({self.calificacion}★)"

    @property
    def nombre(self):
        return f"{self.usuario.first_name} {self.usuario.last_name}"

class TokenReseña(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.UUIDField(unique=True,blank=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Token para {self.usuario.first_name} {self.usuario.last_name} - {self.producto.nombre} - {self.token}"

class Proveedor(models.Model):
    nombre = models.CharField(max_length=50)
    direccion = models.CharField(max_length=100,null=True,blank=True)
    telefono = models.CharField(max_length=15,null=True,blank=True)
    email = models.EmailField(null=True,blank=True)
    cuit = models.CharField(max_length=20,null=True,blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
    
    def __str__(self):
        return self.nombre

class IngresoStock(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='ingresos_stock')
    variante = models.ForeignKey(Variante, on_delete=models.SET_NULL,null=True, blank=True, related_name='ingresos_stock')
    cantidad = models.PositiveIntegerField()
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ingreso de Stock"
        verbose_name_plural = "Ingresos de Stock"
        ordering = ['-fecha_ingreso']
    
    def clean(self):
        if self.variante and self.variante.producto != self.producto:
            raise ValidationError(f"La variante '{self.variante}' no pertenece al producto '{self.producto.nombre}'.")

        if self.producto.variantes.exists() and not self.variante:
            raise ValidationError(f"El producto '{self.producto.nombre}' tiene variantes. Debes especificar cuál estás ingresando (Color/Talle).")
        
        if not self.producto.variantes.exists() and self.variante:
             raise ValidationError("Este producto es simple, no debería tener variante asignada.")

    def save(self, *args, **kwargs):
        if self.variante and not self.producto_id:
            self.producto = self.variante.producto
            
        self.full_clean()
        super().save(*args, **kwargs)
        
        if not self.lotes.exists():
            LoteStock.objects.create(
                ingreso=self,
                cantidad_disponible=self.cantidad,
                costo_unitario=self.costo_unitario,
                fecha_ingreso=self.fecha_ingreso
            )

    def __str__(self):
        item = self.variante.sku if self.variante else self.producto.sku
        return f"Ingreso: {self.cantidad} x {item}"

class LoteStock(models.Model):
    ingreso = models.ForeignKey(IngresoStock, on_delete=models.CASCADE, related_name='lotes')
    cantidad_disponible = models.PositiveIntegerField()
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_ingreso = models.DateTimeField()

    class Meta:
        ordering = ['fecha_ingreso']

    def __str__(self):
        return f"Lote {self.id}"

class MovimientoStock(models.Model):
    class Tipo(models.TextChoices):
        INGRESO = "INGRESO", "Ingreso"
        SALIDA = "SALIDA", "Salida"
        AJUSTE_POSITIVO = "AJUSTE_POSITIVO", "Ajuste +"
        AJUSTE_NEGATIVO = "AJUSTE_NEGATIVO", "Ajuste -"
    
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    variante = models.ForeignKey(Variante, on_delete=models.SET_NULL,null=True, blank=True,)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    cantidad = models.PositiveIntegerField()
    lote = models.ForeignKey(LoteStock, on_delete=models.SET_NULL, null=True, blank=True)
    venta = models.ForeignKey('payment.Venta', on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo}: {self.producto.nombre} x {self.cantidad} -{self.fecha.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-fecha']

class AjusteStock(models.Model):
    venta = models.ForeignKey('payment.Venta', on_delete=models.CASCADE, related_name='ajustes_stock')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    variante = models.ForeignKey(Variante, on_delete=models.SET_NULL, null=True, blank=True,)
    cantidad_faltante = models.IntegerField()
    creado_en = models.DateTimeField(auto_now_add=True)
    resuelto = models.BooleanField(default=False)

    def __str__(self):
        return f"Faltante {self.cantidad_faltante} de {self.producto.nombre} en venta {self.venta.id}"
