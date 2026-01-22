from django.db import models
from django.utils.timezone import localtime
from django.utils.text import slugify
from django.utils import timezone
from django.core.exceptions import ValidationError
from colorfield.fields import ColorField
from django.utils.html import format_html
from django.templatetags.static import static

def validate_image_size(image):
    file_size = image.size
    limit_mb = 2
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(f"La imagen es demasiado pesada. El límite es {limit_mb}MB.")

class Tienda(models.Model):
    """
    Configuración general de la tienda.
    """
    class Divisas(models.TextChoices):
        ARS = 'ARS', 'Pesos Argentinos (ARS)'
        USD = 'USD', 'Dólares Estadounidenses (USD)'

    nombre_tienda = models.CharField(max_length=100, default="Mi Tienda")
    color_primario = ColorField(default="#1173d4",verbose_name="Color Primario")
    color_secundario = ColorField(default="#1987ee",verbose_name="Color Secundario")
    modo_stock = models.CharField(max_length=20, choices=[('libre', 'Sin control de stock'), ('estricto', 'Control de stock')], default='libre')
    mostrar_stock_en_front = models.BooleanField(default=False, help_text="Mostrar cantidad de stock en el sitio.")
    borrar_cupon = models.BooleanField(default=False, help_text="Borrar el cupón después de su uso.")
    mantenimiento = models.BooleanField(default=False, help_text="Indica si el sitio está en modo mantenimiento.")
    divisa = models.CharField(max_length=3, choices=Divisas.choices, default=Divisas.ARS, help_text="Divisa utilizada en la tienda.")
    valor_dolar = models.DecimalField(max_digits=10, decimal_places=2, default=1.0, help_text="Valor actual del dólar.")
    maximo_compra = models.PositiveIntegerField(default=10, help_text="Cantidad máxima de productos por compra(Valor tope cuando se usa el 'modo libre').")
    fecha_actualizacion_dolar = models.DateTimeField(auto_now=True)
    fecha_actualizacion_config = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mi Tienda"
        verbose_name_plural = "Mi Tienda"

    def __str__(self):
        return f"{self.nombre_tienda}"
    
class EventosPromociones(models.Model):
    """
    Eventos y promociones especiales.
    """
    nombre_evento = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    activo = models.BooleanField(default=False)
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, help_text="Descuento en porcentaje (0-100).", null=True, blank=True)
    descuento_fijo = models.DecimalField(max_digits=10, decimal_places=2, help_text="Descuento en valor fijo.", null=True, blank=True)
    mostrar_en_inicio = models.BooleanField(default=False, help_text="Mostrar en la página de inicio.")
    logo = models.ImageField(upload_to='eventos_banners/', help_text="Imagen de banner para el evento/promoción.", null=True, blank=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_logo = self.logo
        
    class Meta:
        verbose_name = "Evento / Promoción"
        verbose_name_plural = "Eventos y Promociones"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        estado = "Activo" if self.esta_activo else "Inactivo"
        return f"{self.nombre_evento} ({estado})"

    @property
    def esta_activo(self):
        """
        Determina si el evento está activo en este momento,
        considerando fechas y el booleano 'activo'.
        """
        ahora = timezone.now()
        return (self.activo and self.fecha_inicio <= ahora <= self.fecha_fin)

    def clean(self):
        """Validaciones de fechas."""
        if self.fecha_fin <= self.fecha_inicio:
            raise ValidationError("La fecha de fin debe ser posterior a la fecha de inicio.")
        if self.descuento_fijo and self.descuento_porcentaje:
            raise ValidationError("Solo se puede definir un tipo de descuento: fijo o porcentaje.")

    def save(self, *args, **kwargs):
        """
        Genera slug automáticamente y valida la coherencia de fechas.
        """
        self.clean()
        self.slug = slugify(self.nombre_evento)
        super().save(*args, **kwargs)

    def __str__(self):
        estado = "Activo" if self.activo else "Inactivo"
        return f"{self.nombre_evento} ({estado}) - Desde {localtime(self.fecha_inicio).strftime('%d/%m/%Y')} hasta {localtime(self.fecha_fin).strftime('%d/%m/%Y')}"

class DatosBancarios(models.Model):
    """
    Información bancaria para pagos.
    """
    banco = models.CharField(max_length=100,default="")
    titular_cuenta = models.CharField(max_length=100,default="")
    numero_cuenta = models.CharField(max_length=50,default="")
    cbu = models.CharField(max_length=50,default="")
    alias = models.CharField(max_length=50,default="")
    imagen_banco = models.ImageField(upload_to='bancos_logos/', help_text="Logo del banco. (Opcional)", null=True, blank=True)

    class Meta:
        verbose_name = "Dato Bancario"
        verbose_name_plural = "Datos Bancarios"

    def __str__(self):
        return f"{self.banco} - {self.titular_cuenta}"

class MercadoPagoConfig(models.Model):
    """
    Configuración de MercadoPago.
    """
    public_key = models.CharField(max_length=200, default="", help_text="Clave pública de MercadoPago.")
    access_token = models.CharField(max_length=200, default="", help_text="Token de acceso de MercadoPago.")
    webhook_key = models.CharField(max_length=200, default="", help_text="Clave para poder recibir pagos.")

    class Meta:
        verbose_name = "Configuración de MercadoPago"
        verbose_name_plural = "Configuraciones de MercadoPago"

    def __str__(self):
        return "MercadoPago"

class HomeSection(models.Model):
    """
    Configuración de secciones en la página de inicio.
    """
    class Tipo(models.TextChoices):
        EMPTY = 'empty', 'Seleccioná una opción'
        BANNER_PRINCIPAL = 'banner_principal', 'Banner Principal'
        GRILLA = 'grilla', 'Grilla de Productos'
        BENTO = 'bento', 'Carousel Tipo Bento'
        STATIC_BENTO = 'static_bento', 'Bento Estático'
        BANNER_MEDIO = "banner_medio", "Banner Pequeño"

    tipo = models.CharField(max_length=50, choices=Tipo.choices)
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en la página de inicio.")
    activo = models.BooleanField(default=True, help_text="Indica si la sección está activa.")
    titulo = models.CharField(max_length=100, blank=True, null=True)
    subtitulo = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        ordering = ["orden"]
        verbose_name = "Sección(Pagina de Inicio)"
        verbose_name_plural = "Secciones(Pagina de Inicio)"

    def clean(self):
        if self.tipo == self.Tipo.EMPTY:
            raise ValidationError("Selecciona un tipo para continuar")

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    TEMPLATES = {
        'banner_principal': 'core/modulos/main_banner.html',
        'grilla': 'core/modulos/grilla.html',
        'bento': 'core/modulos/bento.html',
        'static_bento': 'core/modulos/staticbento.html',
        'banner_medio': 'core/modulos/medium_banners.html'
    } 

    def template(self):
        template = self.TEMPLATES.get(self.tipo)
        return template

    def __str__(self):
        return f"{self.orden} - {self.get_tipo_display()}"

class HomeProductGrid(models.Model):

    class Criterio(models.TextChoices):
        RECIENTES = 'recientes', 'Nuevos Ingresos'
        OFERTAS = 'ofertas', 'Con Descuento'
        DESTACADOS = 'destacados', 'Destacados (Manual)'
        ETIQUETA = 'etiqueta', 'Por Etiqueta Específica'
        MARCA = 'marca', 'Por Marca Específica'
        EVENTO = 'evento', 'Por evento activo'

    seccion = models.ForeignKey(HomeSection, on_delete=models.CASCADE, related_name="grids_productos")
    criterio = models.CharField(max_length=20, choices=Criterio.choices)
    
    etiqueta_filtro = models.ForeignKey('products.Etiquetas', null=True, blank=True, on_delete=models.SET_NULL)
    marca_filtro = models.ForeignKey('products.Marca', null=True, blank=True, on_delete=models.SET_NULL)
    
    def admin_portada(self):
        img_url = static('img/admin/home/grilla.png')
        return format_html(
            "<img src='{}' width='600' style='object-fit: cover;border-radius: 5px;' />",
            img_url
        )
    
    class Meta:
        verbose_name = "Grilla de productos"
        verbose_name_plural = "Grillas de productos"

class HomeBanner(models.Model):
    seccion = models.ForeignKey(
        HomeSection,
        on_delete=models.CASCADE,
        related_name="banners"
    )

    imagen_desktop = models.ImageField(upload_to="home/banners/",validators=[validate_image_size])
    imagen_mobile = models.ImageField(upload_to="home/banners/mobile/",validators=[validate_image_size])
    url = models.URLField(blank=True, null=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden"]
        verbose_name = "Banner de la Página de Inicio"
        verbose_name_plural = "Banners de la Página de Inicio"

    def admin_portada(self):
        img_url = self.imagen_desktop.url if self.imagen_desktop else ''
        return format_html(
            "<img src='{}' width='600' style='object-fit: cover;border-radius: 5px;' />",
            img_url
        )

    def save(self, *args, **kwargs):
        from .utils import compress_image
        if self.pk:
            old = HomeBanner.objects.filter(pk=self.pk).first()
            if old and old.imagen_desktop != self.imagen_desktop:
                self.imagen_desktop = compress_image(self.imagen_desktop, max_width=1200, is_banner=True)
            
            if old and old.imagen_mobile != self.imagen_mobile:
                self.imagen_mobile = compress_image(self.imagen_mobile, max_width=600, is_banner=True)
        else:
            if self.imagen_desktop:
                self.imagen_desktop = compress_image(self.imagen_desktop, max_width=1200, is_banner=True)
            if self.imagen_mobile:
                self.imagen_mobile = compress_image(self.imagen_mobile, max_width=600, is_banner=True)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Banner de {self.seccion} ({self.orden})"

class HomeBannerMedio(models.Model):
    class Tipo(models.TextChoices):
        GARANTIA = "garantia", "Garantía"
        ENVIO = "envio", "Envío"
        CUOTAS = "cuotas", "Cuotas"
        PERSONALIZADO = "personalizado", "Personalizado"
    
    def validate_svg(value):
        if "<script" in value.lower():
            raise ValidationError("No se permiten scripts en SVG.")
        if "onload=" in value.lower() or "onclick=" in value.lower():
            raise ValidationError("Atributos con eventos no permitidos.")

    seccion = models.ForeignKey(HomeSection,on_delete=models.CASCADE,related_name="banners_medios")
    svg = models.TextField(help_text="Código SVG para el ícono del banner.",validators=[validate_svg],default="",null=True,blank=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, unique=True)
    titulo = models.CharField(max_length=40)
    descripcion = models.CharField(max_length=100)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden"]
        verbose_name = "Banner Medio(Garantia, Envío, Cuotas, Personalizado)"
        verbose_name_plural = "Banners Medios(Garantia, Envío, Cuotas, Personalizado)"

    CONFIG = {
        'cuotas': '<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="none"  stroke="currentColor"  stroke-width="1.5"  stroke-linecap="round"  stroke-linejoin="round"  class="icon icon-tabler icons-tabler-outline icon-tabler-credit-card"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 5m0 3a3 3 0 0 1 3 -3h12a3 3 0 0 1 3 3v8a3 3 0 0 1 -3 3h-12a3 3 0 0 1 -3 -3z" /><path d="M3 10l18 0" /><path d="M7 15l.01 0" /><path d="M11 15l2 0" /></svg>',
        'garantia': '<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="none"  stroke="currentColor"  stroke-width="1.5"  stroke-linecap="round"  stroke-linejoin="round"  class="icon icon-tabler icons-tabler-outline icon-tabler-shield"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 3a12 12 0 0 0 8.5 3a12 12 0 0 1 -8.5 15a12 12 0 0 1 -8.5 -15a12 12 0 0 0 8.5 -3" /></svg>',
        'envio': '<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="none"  stroke="currentColor"  stroke-width="1.5"  stroke-linecap="round"  stroke-linejoin="round"  class="icon icon-tabler icons-tabler-outline icon-tabler-truck"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 17m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M17 17m-2 0a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /><path d="M5 17h-2v-11a1 1 0 0 1 1 -1h9v12m-4 0h6m4 0h2v-6h-8m0 -5h5l3 5" /></svg>',
        'personalizado': 'custom'
    }

    def admin_portada(self):
        svg = self.CONFIG.get(self.tipo,{})
        if svg == 'custom':
            svg = self.svg
        return format_html(svg)

    def __str__(self):
        return "Banner Medio de la Página de Inicio"

class HomeCarouselBento(models.Model):
    seccion = models.ForeignKey(
        HomeSection,
        on_delete=models.CASCADE,
        related_name="categorias"
    )

    categoria = models.ForeignKey(
        'products.Categoria',
        on_delete=models.CASCADE,
        related_name="home_items",
        blank=True,
        null=True
    )
    subcategoria = models.ForeignKey(
        'products.SubCategoria',
        on_delete=models.CASCADE,
        related_name="home_items",
        blank=True,
        null=True
    )
    marca = models.ForeignKey(
        'products.Marca',
        on_delete=models.CASCADE,
        related_name="home_items",
        blank=True,
        null=True
    )
    producto = models.ForeignKey(
        'products.Producto',
        on_delete=models.CASCADE,
        related_name="home_items",
        blank=True,
        null=True
    )

    imagen = models.ImageField(upload_to="home/categorias/",validators=[validate_image_size])

    class Tamano(models.TextChoices):
        DEFAULT = "default", "Standard ■"
        LARGE = "large", "Grande ▉"
        TALL = "tall", "Alta ▐"
        WIDE = "wide", "Ancha ▃"

    tamano = models.CharField(
        max_length=20, choices=Tamano.choices, default=Tamano.DEFAULT
    )

    slide = models.PositiveIntegerField(default=1)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["slide", "orden"]
        verbose_name = "Carousel tipo Bento"
        verbose_name_plural = "Carousel tipo Bento"
    
    @property
    def link(self):
        return self.producto or self.categoria or self.marca or self.subcategoria
    
    def admin_portada(self):
        img_url = self.imagen.url if self.imagen else ''
        return format_html(
            "<img src='{}' width='150' style='object-fit: cover;border-radius: 5px;' />",
            img_url
        )

    def clean(self):
        opciones_elegidas = [
            self.producto, 
            self.categoria, 
            self.subcategoria, 
            self.marca
        ]

        elegidos = [x for x in opciones_elegidas if x is not None]

        if len(elegidos) > 1:
            raise ValidationError("¡Error! Solo puedes vincular un destino a la vez (ej: O eliges Producto O eliges Marca, no ambos).")
        if len(elegidos) == 0:
            raise ValidationError("Debes seleccionar al menos un destino para el banner.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"(Slide {self.slide})"

class HomeStaticBento(models.Model):
    seccion = models.ForeignKey(
        HomeSection,
        on_delete=models.CASCADE,
        related_name="static_bento"
    )

    categoria = models.ForeignKey(
        'products.Categoria',
        on_delete=models.CASCADE,
        related_name="static_home_items",
        blank=True,
        null=True
    )
    subcategoria = models.ForeignKey(
        'products.SubCategoria',
        on_delete=models.CASCADE,
        related_name="static_home_items",
        blank=True,
        null=True
    )
    marca = models.ForeignKey(
        'products.Marca',
        on_delete=models.CASCADE,
        related_name="static_home_items",
        blank=True,
        null=True
    )
    producto = models.ForeignKey(
        'products.Producto',
        on_delete=models.CASCADE,
        related_name="static_home_items",
        blank=True,
        null=True
    )

    imagen = models.ImageField(upload_to="home/categorias/",validators=[validate_image_size])
    color_fondo = models.CharField(default="#ffffff",max_length=7, help_text="Color HEX (ej: #2e6fc3)")
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden"]
        verbose_name = "Bento Estatico"
        verbose_name_plural = "Bento Estatico"

    @property
    def link(self):
        return self.producto or self.categoria or self.marca or self.subcategoria

    def admin_portada(self):
        img_url = self.imagen.url if self.imagen else ''
        return format_html(
            "<img src='{}' width='150' style='object-fit: cover;border-radius: 5px;' />",
            img_url
        )
    
    def clean(self):
        opciones_elegidas = [
            self.producto, 
            self.categoria, 
            self.subcategoria, 
            self.marca
        ]

        elegidos = [x for x in opciones_elegidas if x is not None]

        if len(elegidos) > 1:
            raise ValidationError("¡Error! Solo puedes vincular un destino a la vez (ej: O eliges Producto O eliges Marca, no ambos).")
        if len(elegidos) == 0:
            raise ValidationError("Debes seleccionar al menos un destino para el banner.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)