from django.db import models
from core.utils import obtener_valor_dolar
from django.utils.text import slugify
from django.urls import reverse
from django.templatetags.static import static
from django.core.cache import cache
import uuid

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
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    precio_dolar = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    descuento = models.IntegerField(default=0)
    sku = models.CharField(max_length=20, unique=True, blank=True, null=True,editable=False)
    descripcion_seo = models.CharField(max_length=160,blank=True,help_text="Descripción corta para SEO (aparece en Google). Máximo 160 caracteres.")
    inhabilitar = models.BooleanField(default=False)
    slug = models.SlugField(max_length=100, blank=True,unique=True)
    proveedor = models.CharField(max_length=30,blank=True,null=True)
    updated_at = models.DateTimeField(auto_now=True)
    etiquetas = models.ManyToManyField(Etiquetas, blank=True, related_name='productos')
    stock = models.PositiveIntegerField(default=0)

    def get_absolute_url(self):
        return reverse('products:slug_dispatcher',args=[self.slug])

    def save(self, *args, **kwargs):
        if self.pk:
            original = Producto.objects.filter(pk=self.pk).first()
            if original and original.nombre != self.nombre:
                self.slug = None

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
        """
        Calcula el precio anterior basado en el valor del dólar.
        El valor del dólar se cachea durante 1 hora para evitar consultas repetidas.
        """
        if not self.precio_dolar:
            return None
        try:
            valor_dolar = cache.get('valor_dolar_actual')
            if valor_dolar is None:
                valor_dolar = obtener_valor_dolar()
                cache.set('valor_dolar_actual', valor_dolar, 3600)
            return round(self.precio_dolar * valor_dolar, 2)
        except Exception:
            return None
        
    def get_stock_disponible(self, color_id=None):
        """
        Retorna el stock disponible del producto o de un color específico.
        """
        if self.colores.exists():
            if color_id:
                color = self.colores.filter(id=color_id).first()
                return color.stock if color else 0
            return sum(c.stock for c in self.colores.all())
        return self.stock

    def get_stock_colores(self):
        """
        Retorna el stock de cada color asociado al producto.
        """
        return [{'color':color.nombre,'stock':color.stock} for color in self.colores.all()]

    def restar_stock(self, cantidad, color_id=None):
        """
        Resta stock del producto o del color específico si se proporciona color_id.
        """
        if self.colores.exists() and color_id:
            color = self.colores.filter(id=color_id).first()
            if not color or color.stock < cantidad:
                raise ValueError(f"Stock insuficiente para {self.nombre} ({color.nombre if color else 'color desconocido'})")
            color.stock -= cantidad
            color.save()
        else:
            if self.stock < cantidad:
                raise ValueError(f"Stock insuficiente para {self.nombre}")
            self.stock -= cantidad
            self.save()

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
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.nombre} ({self.producto})"
    
class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes_producto',  blank=True)
    color = models.ForeignKey(ColorProducto,on_delete=models.CASCADE,related_name='imagenes_color',null=True,blank=True)
    imagen = models.ImageField(upload_to='productos/imagenes/')
    imagen_200 = models.ImageField(upload_to='productos/imagenes/', null=True, blank=True,editable=False)

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