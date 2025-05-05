from re import T
from django.db import models
from core.utils import obtener_valor_dolar
from django.utils.text import slugify

class Marca(models.Model):
    nombre = models.CharField(max_length=30)
    imagen = models.ImageField(upload_to='marcas/', default='marcas/default.jpg')

    def __str__(self):
        return self.nombre

class Categoria(models.Model):

    SECCIONES_MENU = [
    ('componentes', 'Componentes'),
    ('computos', 'PC y Notebooks'),
    ('accesorios', 'Accesorios'),
    ('dispositivos', 'Dispositivos'),
    ('impresion', 'Impresión'),
    ]

    nombre = models.CharField(max_length=30)
    descripcion_seo = models.CharField(
    max_length=160,
    blank=True,
    help_text="Descripción corta para SEO (aparece en Google). Máximo 160 caracteres."
    )
    slug = models.SlugField(max_length=50, blank=True,unique=True)
    seccion_id = models.CharField(max_length=50, blank=True, null=True,choices=SECCIONES_MENU)
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en el menú")

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
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    precio_dolar = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    descuento = models.IntegerField(default=0)
    sku = models.CharField(max_length=20, unique=True, blank=True, null=True,editable=False)
    portada = models.ImageField(upload_to='productos/portadas/',null=True, blank=True)
    descripcion_seo = models.CharField(max_length=160,blank=True,help_text="Descripción corta para SEO (aparece en Google). Máximo 160 caracteres.")
    inhabilitar = models.BooleanField(default=False)
    slug = models.SlugField(max_length=100, blank=True,unique=True)
    proveedor = models.CharField(max_length=30,blank=True,null=True)

    def save(self, *args, **kwargs):
        # Detectar si cambió el nombre
        if self.pk:
            original = Producto.objects.filter(pk=self.pk).first()
            if original and original.nombre != self.nombre:
                self.slug = None  # Forzamos que se regenere

        self.generar_slug()
        super().save(*args, **kwargs)

    def generar_slug(self):
        if not self.slug:
            base_slug = slugify(self.nombre)
            slug = base_slug
            i = 1
            while Producto.objects.exclude(id=self.id).filter(slug=slug).exists():
                slug = f"{base_slug}-{i}"
                i += 1
            self.slug = slug

    @property
    def precio_anterior(self):
        if self.precio_dolar:
            try:
                return round(self.precio_dolar * obtener_valor_dolar(), 2)
            except:
                return None
        return None

    def __str__(self):
        return self.nombre

class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes',  blank=True)
    imagen = models.ImageField(upload_to='productos/imagenes/')
    imagen_100 = models.ImageField(upload_to='productos/imagenes/', null=True, blank=True,editable=False)

class Atributo(models.Model):
    producto = models.ForeignKey(Producto, related_name="atributos", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    valor = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre}: {self.valor}"

class Etiquetas(models.Model):
    producto = models.ForeignKey(Producto, related_name="etiquetas", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

class CategoriaEspecificacion(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class EspecificacionTecnica(models.Model):
    producto = models.ForeignKey(Producto, related_name='especificaciones', on_delete=models.CASCADE)
    categoria = models.ForeignKey(CategoriaEspecificacion, on_delete=models.SET_NULL, null=True, blank=True)
    datos = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        categoria_nombre = self.categoria.nombre if self.categoria else 'Sin categoría'
        return f"{categoria_nombre} ({self.producto.nombre})"