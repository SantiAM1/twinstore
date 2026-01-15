from django.db import models
from django.utils.timezone import localtime
from django.utils.text import slugify
from django.utils import timezone
from django.core.exceptions import ValidationError

class Tienda(models.Model):
    """
    Configuración general de la tienda.
    """
    class Divisas(models.TextChoices):
        ARS = 'ARS', 'Pesos Argentinos (ARS)'
        USD = 'USD', 'Dólares Estadounidenses (USD)'

    nombre_tienda = models.CharField(max_length=100, default="Mi Tienda")
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
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio.")
        if self.descuento_fijo and self.descuento_porcentaje:
            raise ValueError("Solo se puede definir un tipo de descuento: fijo o porcentaje.")

    def save(self, *args, **kwargs):
        """
        Genera slug automáticamente y valida la coherencia de fechas.
        """
        self.slug = slugify(self.nombre_evento)
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        estado = "Activo" if self.activo else "Inactivo"
        return f"{self.nombre_evento} ({estado}) - Desde {localtime(self.fecha_inicio).strftime('%d/%m/%Y')} hasta {localtime(self.fecha_fin).strftime('%d/%m/%Y')}"

class DatosBancarios(models.Model):
    """
    Información bancaria para pagos.
    """
    banco = models.CharField(max_length=100)
    titular_cuenta = models.CharField(max_length=100)
    numero_cuenta = models.CharField(max_length=50)
    cbu = models.CharField(max_length=50)
    alias = models.CharField(max_length=50)
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
    modo_sandbox = models.BooleanField(default=True, help_text="Indica si se está en modo sandbox (pruebas).")
    public_key = models.CharField(max_length=200, help_text="Clave pública de MercadoPago.")
    access_token = models.CharField(max_length=200, help_text="Token de acceso de MercadoPago.")

    class Meta:
        verbose_name = "Configuración de MercadoPago"
        verbose_name_plural = "Configuraciones de MercadoPago"

    def __str__(self):
        entorno = "Sandbox" if self.modo_sandbox else "Producción"
        return f"MercadoPago ({entorno})"

class HomeSection(models.Model):
    """
    Configuración de secciones en la página de inicio.
    """
    class Tipo(models.TextChoices):
        BANNER_PRINCIPAL = 'banner_principal', 'Banner Principal'
        OFERTAS = 'ofertas', 'Ofertas'
        PRODUCTOS_DESTACADOS = 'productos_destacados', 'Productos Destacados'
        CATEGORIAS = 'categorias', 'Categorías'
        NUEVOS_PRODUCTOS = 'nuevos_productos', 'Nuevos Productos'
        BANNER_MEDIO = "banner_medio", "Banner Intermedio"
        MARCAS = "marcas", "Marcas Destacadas"
        TEXTO_SEO = "texto_seo", "Texto SEO"
        PERSONALIZADO1 = "custom1", "Personalizado 1"
        PERSONALIZADO2 = "custom2", "Personalizado 2"

    tipo = models.CharField(max_length=50, choices=Tipo.choices)
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en la página de inicio.")
    activo = models.BooleanField(default=True, help_text="Indica si la sección está activa.")
    titulo = models.CharField(max_length=100, blank=True, null=True)
    subtitulo = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        ordering = ["orden"]
        verbose_name = "Sección(Pagina de Inicio)"
        verbose_name_plural = "Secciones(Pagina de Inicio)"

    def __str__(self):
        return f"{self.orden} - {self.get_tipo_display()}"

class HomeBanner(models.Model):
    seccion = models.ForeignKey(
        HomeSection,
        on_delete=models.CASCADE,
        related_name="banners"
    )

    imagen_desktop = models.ImageField(upload_to="home/banners/")
    imagen_mobile = models.ImageField(upload_to="home/banners/mobile/")
    url = models.URLField(blank=True, null=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden"]
        verbose_name = "Banner de la Página de Inicio"
        verbose_name_plural = "Banners de la Página de Inicio"

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
    svg = models.TextField(help_text="Código SVG para el ícono del banner.",validators=[validate_svg],default="")
    tipo = models.CharField(max_length=20, choices=Tipo.choices, unique=True)
    titulo = models.CharField(max_length=40)
    descripcion = models.CharField(max_length=100)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden"]
        verbose_name = "Banner Medio(Garantia, Envío, Cuotas, Personalizado)"
        verbose_name_plural = "Banners Medios(Garantia, Envío, Cuotas, Personalizado)"

    def __str__(self):
        return "Banner Medio de la Página de Inicio"

class HomeCategoryItem(models.Model):
    seccion = models.ForeignKey(
        HomeSection,
        on_delete=models.CASCADE,
        related_name="categorias"
    )

    categoria = models.ForeignKey(
        'products.Categoria',
        on_delete=models.CASCADE,
        related_name="home_items"
    )
    subcategoria = models.ForeignKey(
        'products.SubCategoria',
        on_delete=models.CASCADE,
        related_name="home_items",
        blank=True,
        null=True
    )

    imagen = models.ImageField(upload_to="home/categorias/")

    class Tamano(models.TextChoices):
        DEFAULT = "default", "Standard"
        LARGE = "large", "Grande"
        TALL = "tall", "Alta"
        WIDE = "wide", "Ancha"

    tamano = models.CharField(
        max_length=20, choices=Tamano.choices, default=Tamano.DEFAULT
    )

    slide = models.PositiveIntegerField(default=1)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["slide", "orden"]
        verbose_name = "Carousel de Categorías|Subcategorias"
        verbose_name_plural = "Carousel de Categorías|Subcategorias"

    def __str__(self):
        return f"{self.nombre} (Slide {self.slide})"

class HomeReseñas(models.Model):
    """
    Configuración de la sección de reseñas en la página de inicio.
    """
    section = models.ForeignKey(
        HomeSection,
        on_delete=models.CASCADE,
        related_name="reseñas"
    )
    titulo = models.CharField(max_length=100, blank=True, null=True)
    subtitulo = models.CharField(max_length=150, blank=True, null=True)
    calificaciones = models.PositiveBigIntegerField(default=0, help_text="Calificacion minima para mostrar reseñas. (0 incluye todo tipo de reseñas)")

    class Meta:
        verbose_name = "Reseñas de Clientes"
        verbose_name_plural = "Reseñas de Clientes"

    def __str__(self):
        return "Sección de Reseñas en la Página de Inicio"

class HomeCarousel(models.Model):
    """
    Configuración de carruseles personalizados en la página de inicio.
    """
    seccion = models.ForeignKey(
        HomeSection,
        on_delete=models.CASCADE,
        related_name="carouseles"
    )
    titulo = models.CharField(max_length=100, blank=True, null=True)
    subtitulo = models.CharField(max_length=150, blank=True, null=True)
    etiqueta = models.ManyToManyField(
        'products.Etiquetas',
        related_name="carouseles_home"
    )

    class Meta:
        verbose_name = "Carrusel Personalizado"
        verbose_name_plural = "Carruseles Personalizados"

    def __str__(self):
        return f"Carrusel de {self.seccion}"