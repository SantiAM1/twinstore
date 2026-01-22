from decimal import Decimal
from .models import Tienda,MercadoPagoConfig,DatosBancarios
from django.core.cache import cache
from django.conf import settings
from django.utils.encoding import smart_str
from django.http import HttpRequest
from .types import ConfigDict
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import connection

def gen_cache_key(key_name, request = None):
    """Genera una key de caché única por tenant, si no hay tenant schema=public"""
    if request and hasattr(request, 'tenant'):
        schema = request.tenant.schema_name
    else:
        schema = getattr(connection, 'schema_name', 'public')


    return f"{schema}:{key_name}"

def build_site_url(schema_name=None):
    if not schema_name:
        schema_name = getattr(connection, 'schema_name', 'public')

    base_domain = settings.SITE_URL.strip("/")

    if schema_name == 'public':
        return base_domain

    return f"{schema_name}.{base_domain}"

def build_absolute_uri(schema_name=None, path=""):
    """
    Construye la URL del sitio basada en el tenant actual.
    Si no hay tenant se envia SITE_URL
    """
    domain = build_site_url(schema_name)
    protocol = "https" if not settings.DEBUG else "http"
    
    if path and not path.startswith("/"):
        path = f"/{path}"
        
    return f"{protocol}://{domain}{path}"

def actualizar_precio_final(producto) -> None:
    """
    Calcula el precio final de un producto basado en la configuración de la tienda y actualiza su atributo 'precio'.
    Args:
        producto (Producto): Instancia del producto cuyo precio se va a actualizar.
    """
    config = get_configuracion_tienda()
    if config['divisa'] == Tienda.Divisas.USD:
        if producto.precio_divisa is None:
            return 

        precio_base = round(producto.precio_divisa * config['valor_dolar'], 2)

        if producto.descuento > 0:
            descuento_decimal = Decimal(producto.descuento) / Decimal('100')
            producto.precio = round(precio_base * (1 - descuento_decimal), 2)
        else:
            producto.precio = precio_base
    else:
        if producto.descuento > 0:
            descuento_decimal = Decimal(producto.descuento) / Decimal('100')
            producto.precio = round(producto.precio_divisa * (1 - descuento_decimal), 2)
        else:
            producto.precio = producto.precio_divisa

def get_configuracion_tienda(request: HttpRequest = None) -> ConfigDict:
    """
    Obtiene la configuración general de la tienda desde caché.
    Si no existe, la crea o la guarda automáticamente.
    """
    CACHE_KEY_CONFIG = gen_cache_key("configuracion_tienda",request)
    config = cache.get(CACHE_KEY_CONFIG)
    if config:
        return config

    config = Tienda.objects.first()
    if not config:
        config = Tienda.objects.create()

    data = {
        'nombre_tienda': config.nombre_tienda,
        'color_primario': config.color_primario,
        'color_secundario': config.color_secundario,
        'modo_stock': config.modo_stock,
        'mostrar_stock_en_front': config.mostrar_stock_en_front,
        'borrar_cupon': config.borrar_cupon,
        'mantenimiento': config.mantenimiento,
        'divisa': config.divisa,
        'valor_dolar': config.valor_dolar,
        'maximo_compra': config.maximo_compra,
    }

    time = 43200 if not settings.DEBUG else 5

    cache.set(CACHE_KEY_CONFIG, data, timeout=time)
    return data

try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE = Image.ANTIALIAS

def resize_to_size(image_field, size=(200, 200)):
    """
    Resize para logos, iconos y elementos gráficos:
    """
    if not image_field:
        return None

    try:
        img = Image.open(image_field)

        if img.mode != "RGBA":
            img = img.convert("RGBA")

        target_w, target_h = size
        original_w, original_h = img.size

        ratio_w = target_w / original_w
        ratio_h = target_h / original_h
        scale = min(ratio_w, ratio_h)

        new_w = int(original_w * scale)
        new_h = int(original_h * scale)

        img = img.resize((new_w, new_h), RESAMPLE)

        canvas = Image.new("RGBA", size, (0, 0, 0, 0))

        left = (target_w - new_w) // 2
        top = (target_h - new_h) // 2
        canvas.paste(img, (left, top), img)

        buffer = BytesIO()
        canvas.save(fp=buffer, format="WEBP", quality=90)

        return ContentFile(buffer.getvalue())

    except Exception as e:
        print("ERROR resize:", e)
        return None
    
def compress_image(image_field, max_width=1200, quality=80, is_banner=False):
    if not image_field:
        return None

    try:
        img = Image.open(image_field)

        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):

            if is_banner:
                img = img.convert('RGB')
            else:
                img = img.convert('RGBA')
        else:
            img = img.convert('RGB')

        original_width, original_height = img.size
        
        if original_width > max_width:
            ratio = max_width / original_width
            new_height = int(original_height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        buffer = BytesIO()
        
        img.save(fp=buffer, format="WEBP", quality=quality, optimize=True) 

        new_name = image_field.name.split('.')[0] + ".webp"
        return ContentFile(buffer.getvalue(), name=new_name)

    except Exception as e:
        print(f"ERROR compress_image: {e}")
        return image_field

def make_tenant_key(key, key_prefix, version):
    """
    Genera una llave de caché que incluye automáticamente el schema actual.
    Ejemplo: 'nike:1:vistas.decorators.cache.cache_header..'
    """
    from django_tenants.utils import get_tenant_model
    from django.db import connection
    
    tenant_schema = connection.schema_name 
    
    return ':'.join([tenant_schema, str(version), smart_str(key_prefix), smart_str(key)])

def get_mp_config() -> dict[str]:
    CACHE_MP_KEY = gen_cache_key('mercado_pago')
    data = cache.get(CACHE_MP_KEY)
    if not data:
        mp_config = MercadoPagoConfig.objects.first()
        data = {
            "access":mp_config.access_token,
            "public":mp_config.public_key,
            "webhook":mp_config.webhook_key
        }
        cache.set(CACHE_MP_KEY, data, 43200)
    return data

def get_datos_banc() -> dict[str]:
    CACHE_BANCO_KEY = gen_cache_key('datos_bancarios')
    data = cache.get(CACHE_BANCO_KEY)
    if not data:
        banco = DatosBancarios.objects.first()
        data = {
            "banco": banco.banco,
            "titular_cuenta": banco.titular_cuenta,
            "cbu": banco.cbu,
            "alias": banco.alias,
        }
        cache.set(CACHE_BANCO_KEY, data, 43200)
    return data