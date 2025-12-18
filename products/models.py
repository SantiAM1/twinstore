from django.db import models,transaction
from django.db.models import Sum
from core.utils import get_configuracion_tienda
from django.utils.text import slugify
from django.urls import reverse
from django.templatetags.static import static
from django.core.cache import cache
import uuid
from decimal import Decimal
from .managers import ProductoManager
from products.utils_debug import debug_queries
from django.contrib.auth.models import User

class Marca(models.Model):
    nombre = models.CharField(max_length=30)
    slug = models.SlugField(max_length=50, blank=True,unique=True)

    def get_absolute_url(self):
        base_url = reverse('products:grid')
        return f"{base_url}?Marca={self.slug}"

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
    evento = models.ForeignKey('core.EventosPromociones',on_delete=models.SET_NULL,blank=True,null=True)
    objects = ProductoManager()

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
        Devuelve {color_hex: stock} si tiene colores, o {'total': stock} si no.
        Optimizado para usar datos precargados si existen.
        """
        stock_dict = {}

        # 1. Obtenemos los colores (aprovechando el caché de prefetch si existe)
        colores = self.colores.all()

        if len(colores) > 0:
            for color in colores:
                if hasattr(color, '_stock_cache'):
                    stock_dict[color.hex] = color._stock_cache
                
                # FALLBACK
                else:
                    stock = (LoteStock.objects.filter(
                        ingreso__producto_color=color,
                        cantidad_disponible__gt=0
                    ).aggregate(t=Sum("cantidad_disponible"))["t"] or 0)
                    stock_dict[color.hex] = stock
            
            return stock_dict

        else:
            if hasattr(self, '_total_stock_cache'):
                return {'total': self._total_stock_cache}
            
            # FALLBACK
            total_stock = (LoteStock.objects.filter(
                ingreso__producto=self,
                cantidad_disponible__gt=0
            ).aggregate(t=Sum("cantidad_disponible"))["t"] or 0)
            
            return {'total': total_stock}

    def obtener_stock(self, color=None) -> int:
        """
        Obtiene el stock disponible del producto o de un color específico si se proporciona.
        """
        if color:
            return (
                LoteStock.objects.filter(
                    ingreso__producto_color=color,
                    cantidad_disponible__gt=0
                ).aggregate(total=Sum("cantidad_disponible"))["total"] or 0
            )

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

    def get_portada_color_200(self):
        """
        Devuelve una lista de diccionarios con los colores y sus respectivas imagenes.
        """
        data = []
        for color in self.colores.all():
            imgs = color.imagenes_color.all()
            imagen = imgs[0] if imgs else None
            if imagen:
                data.append({'hex': color.hex, 'url': imagen.imagen_200.url if imagen.imagen_200 else imagen.imagen.url})
            else:
                data.append({'hex': color.hex, 'url': static('img/prod_default.webp')})
        return data

    def get_imagen_carro(self, color_id=None):
        """
        Retorna la imagen del producto para el carro de compras,
        usando datos prefetchados si existen.
        """
        if color_id:
            color = next((c for c in self.colores.all() if c.id == color_id), None)
            if color:
                imagenes_color = list(color.imagenes_color.all())
                if imagenes_color:
                    imagen = imagenes_color[0]
                    return imagen.imagen_200.url if imagen.imagen_200 else imagen.imagen.url

        imagenes = list(self.imagenes_producto.all())
        if imagenes:
            imagen = imagenes[0]
            return imagen.imagen_200.url if imagen.imagen_200 else imagen.imagen.url

        return static('img/prod_default.webp')

    def obtener_imagenes(self):
        """
        Retorna un diccionario con imágenes agrupadas por color, 
        usando relaciones ya prefetchadas (sin nuevas queries).
        """
        if self.colores.exists():
            data = {}
            for color in list(self.colores.all()):
                imagenes = list(color.imagenes_color.all())
                data[color.id] = {
                    'nombre': color.nombre,
                    'hex': color.hex,
                    'imagenes': imagenes
                }
            return data
        else:
            return {'imagenes': list(self.imagenes_producto.all())}

    def __str__(self):
        return self.nombre

class ColorProducto(models.Model):
    producto = models.ForeignKey(Producto,on_delete=models.CASCADE,related_name='colores')
    nombre = models.CharField(max_length=50)
    hex = models.CharField(max_length=7,help_text='Color en HEXADECIMAL (#ffffff)',default='#ffffff')

    class Meta:
        verbose_name = "Color"
        verbose_name_plural = "Colores"

    def __str__(self):
        return f"{self.nombre} ({self.producto})"
    
class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes_producto',  blank=True)
    color = models.ForeignKey(ColorProducto,on_delete=models.CASCADE,related_name='imagenes_color',null=True,blank=True)
    imagen = models.ImageField(upload_to='productos/imagenes/')
    imagen_200 = models.ImageField(upload_to='productos/imagenes/', null=True, blank=True,editable=False)

    class Meta:
        verbose_name = "Imagen"
        verbose_name_plural = "Imagenes"

class Atributo(models.Model):
    producto = models.ForeignKey(Producto, related_name="atributos", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    valor = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}: {self.valor}"

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
    usuario = models.ForeignKey("users.PerfilUsuario", on_delete=models.CASCADE, null=True, blank=True)
    comentario = models.TextField(max_length=250)
    calificacion = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reseña"
        verbose_name_plural = "Reseñas"
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.producto.nombre} - {self.usuario.nombre if self.usuario else 'Anonimo'} ({self.calificacion}★)"

    @property
    def nombre(self):
        return f"{self.usuario.nombre} {self.usuario.apellido}"

class TokenReseña(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    usuario = models.ForeignKey("users.PerfilUsuario", on_delete=models.CASCADE)
    token = models.UUIDField(unique=True,blank=True,editable=False)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Token para {self.usuario.nombre} - {self.producto.nombre} - {self.token}"

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
    producto_color = models.ForeignKey(ColorProducto, on_delete=models.CASCADE, null=True, blank=True, related_name='ingresos_stock')
    cantidad = models.PositiveIntegerField()
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ingreso de Stock"
        verbose_name_plural = "Ingresos de Stock"
        ordering = ['-fecha_ingreso']

    def __str__(self):
        return f"Ingreso: {self.cantidad} x {self.producto.nombre} | {self.fecha_ingreso.strftime('%Y-%m-%d') if self.fecha_ingreso else ''}"

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
    producto_color = models.ForeignKey(ColorProducto, on_delete=models.PROTECT, null=True, blank=True)
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
    color = models.ForeignKey(ColorProducto, on_delete=models.PROTECT, null=True, blank=True)
    cantidad_faltante = models.IntegerField()
    creado_en = models.DateTimeField(auto_now_add=True)
    resuelto = models.BooleanField(default=False)

    def __str__(self):
        return f"Faltante {self.cantidad_faltante} de {self.producto.nombre} en venta {self.venta.id}"
