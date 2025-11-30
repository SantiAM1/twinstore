from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.http import HttpRequest
from django.core.cache import cache
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import cache_page
from django.db.models import Prefetch
from django.utils import timezone

from .throttling import PrediccionBusquedaThrottle
from .utils import get_configuracion_tienda
from .forms import ExcelUploadForm,DolarActualizar
from .permissions import BloquearSiMantenimiento
from .models import Tienda,EventosPromociones

from products.models import Producto, Marca, SubCategoria, Atributo,Etiquetas

from rest_framework.views import APIView
from rest_framework.response import Response

import pandas as pd
import uuid
import re
from decimal import Decimal, InvalidOperation
import unicodedata
# Create your views here.

@cache_page(60 * 15)
def contacto(request):
    return render(request,'core/contacto.html')

@cache_page(60 * 15)
def politicas_tecnico(request):
    return render(request,'core/politicas/politicas-tecnico.html')

@cache_page(60 * 15)
def boton_arrepentimiento(request):
    return render(request,'core/politicas/arrepentimiento.html')

@cache_page(60 * 15)
def terminos_condiciones(request):
    return render(request,'core/politicas/terminos-condiciones.html')

@cache_page(60 * 15)
def preguntas_frecuentes(request):
    return render(request,'core/politicas/faq.html')

@cache_page(60 * 15)
def politicas_envios(request):
    return render(request, 'core/politicas/politicas-envios.html')

@cache_page(60 * 15)
def politicas_devolucion(request):
    return render(request,'core/politicas/politicas-devolucion.html')

@cache_page(60 * 15)
def politicas_priv(request):
    return render(request,'core/politicas/politicas-privacidad.html')

def pagina_mantenimiento(request):
    return render(request, 'core/mantenimiento.html')

def normalize_text(text: str) -> str:
    """
    Normaliza texto eliminando tildes, símbolos y lower-case.
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    return text.lower()


class BusquedaPredictivaView(APIView):
    throttle_classes = [PrediccionBusquedaThrottle]
    permission_classes = [BloquearSiMantenimiento]

    def get(self, request):
        q = request.GET.get('q', '').strip()
        if not q or len(q) < 2:
            return Response([])

        q = normalize_text(q)
        tokens = [t for t in q.replace("-", " ").split() if t]

        productos = cache.get('productos_busqueda')

        if not productos:
            productos_raw = list(
                Producto.objects
                .values(
                    'nombre',
                    'slug',
                    'imagenes_producto__imagen_200',
                    'precio_final',
                )
                .order_by('-precio_final')
            )

            productos_dict = {}
            for p in productos_raw:
                slug = p['slug']
                if slug not in productos_dict:
                    productos_dict[slug] = p

            productos = list(productos_dict.values())

            for p in productos:
                img = p.get('imagenes_producto__imagen_200')
                if img:
                    p['imagenes_producto__imagen_200'] = f"{settings.MEDIA_URL}{img}"

                p["search"] = normalize_text(f"{p['nombre']} {p['slug']}")

            cache.set('productos_busqueda', productos, 300)

        resultados = []
        for p in productos:
            search = p['search']
            score = 0

            for token in tokens:
                if token == search:
                    score += 50  # coincidencia perfecta
                elif token in search.split():
                    score += 25  # palabra exacta
                elif search.startswith(token):
                    score += 15  # prefix
                elif token in search:
                    score += 10  # substring

            if score > 0:
                p['_score'] = score
                resultados.append(p)

        resultados.sort(
            key=lambda x: (x['_score'], x['precio_final'], bool(x["imagenes_producto__imagen_200"])),
            reverse=True
        )

        return Response(resultados[:10])

def home(request):
    home_cache = cache.get('home_cache')
    if not home_cache:
        home_cache = {
            'ofertas': Producto.objects.filter(descuento__gt=0).prefetch_related("colores__imagenes_color","imagenes_producto"),
            'destacados': Producto.objects.filter(etiquetas__slug='destacado').prefetch_related("colores__imagenes_color","imagenes_producto"),
        }
        cache.set('home_cache', home_cache, 60 * 30)

    return render(request,'core/inicio.html', {'destacados': home_cache['destacados'], 'ofertas': home_cache['ofertas']})

@staff_member_required
def cache_clear(request):
    cache.clear()
    messages.success(request, "Cache limpiada correctamente.")
    return redirect('core:home')

@staff_member_required
def test(request):
    ahora = timezone.now()

    eventos_activos = EventosPromociones.objects.filter(
        activo=True,
        fecha_inicio__lte=ahora,
        fecha_fin__gte=ahora,
    )

    productos = (
        Producto.objects.all()
        .prefetch_related(
            "colores__imagenes_color",
            "imagenes_producto",
            "etiquetas",
            Prefetch(
                "etiquetas__eventos",
                queryset=eventos_activos,
                to_attr="eventos_filtrados"
            )
        )
    )

    return render(request, "core/test.html", {"productos": productos})

@staff_member_required
def cargar_productos_excel(request):
    if request.method == 'POST':
        excel = ExcelUploadForm(request.POST, request.FILES)
        if excel.is_valid():
            archivo = excel.cleaned_data['archivo']
            if archivo is not None:
                try:
                    df = pd.read_excel(archivo)

                    if df.empty:
                        messages.error(request, "El archivo Excel está vacío.")
                        return redirect('core:cargar_excel')

                    token_columna = df.get('Token')
                    if token_columna is None or token_columna.isna().all():
                        messages.error(request, "El archivo no contiene un campo 'Token'.")
                        return redirect('core:cargar_excel')

                    token_archivo = str(token_columna.dropna().iloc[0]).strip()

                    if token_archivo != settings.EXCEL_TOKEN:
                        messages.error(request, "Token inválido. No se cargó el archivo.")
                        return redirect('core:cargar_excel')

                    nombres_en_excel = df['Producto'].tolist()
                    productos_existentes = Producto.objects.all()
                    productos_a_eliminar = productos_existentes.exclude(nombre__in=nombres_en_excel)
                    eliminados = productos_a_eliminar.count()

                    for eliminado in productos_a_eliminar:
                        messages.error(request, mark_safe(f'❌ Producto <strong>{eliminado.nombre}</strong> eliminado'))

                    productos_a_eliminar.delete()

                    Atributo.objects.all().delete()
                    Etiquetas.objects.all().delete()

                    for _, fila in df.iterrows():
                        marca, _ = Marca.objects.get_or_create(nombre=fila['Marca'])

                        try:
                            sub_categoria = SubCategoria.objects.get(nombre=fila['Sub-categoria'])
                        except SubCategoria.DoesNotExist:
                            messages.warning(request, f'Subcategoría no encontrada: {fila["Sub-categoria"]}')
                            continue

                        sku = f"{marca.nombre[:3].upper()}-{sub_categoria.nombre[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"

                        config = get_configuracion_tienda()

                        inhabilitar_str = str(fila.get('Inhabilitar', '')).strip().lower()
                        inhabilitar_flag = inhabilitar_str in ['si', 'sí', 'true', '1']

                        try:
                            precio_raw = fila.get('Precio', '')
                            precio_str = str(precio_raw).replace(',', '.')
                            precio_excel = Decimal(precio_str)

                        except (InvalidOperation, TypeError, ValueError) as e:
                            messages.error(request, f"❌ Error al convertir el precio: {fila.get('Precio')} → {e}")
                            continue

                        try:
                            descuento_raw = fila.get('Descuento', '0')
                            descuento_str = str(descuento_raw).replace(',', '.')
                            descuento_excel = Decimal(descuento_str)
                        except (InvalidOperation, TypeError, ValueError) as e:
                            messages.error(request, f"❌ Error al convertir el descuento: {fila.get('Descuento')} → {e}")
                            continue

                        producto, creado = Producto.objects.get_or_create(
                            nombre=fila['Producto'],
                            defaults={
                                'marca': marca,
                                'sub_categoria': sub_categoria,
                                'precio_divisa': precio_excel,
                                'precio': precio_excel if config['divisa'] == Tienda.Divisas.ARS else None,
                                'descuento': fila['Descuento'],
                                'sku': sku,
                                'inhabilitar': inhabilitar_flag
                            }
                        )

                        if creado:
                            messages.success(request, mark_safe(f'✅ Producto <strong>{producto.nombre}</strong> agregado'))
                        else:
                            inhabilitar_str = str(fila.get('Inhabilitar', '')).strip().lower()
                            producto.inhabilitar = inhabilitar_str in ['si', 'sí', 'true', '1']
                            producto.save(update_fields=['inhabilitar'])
                            if not producto.slug:
                                producto.generar_slug()
                                producto.save()
                            descuento_excel = fila['Descuento']

                            hubo_cambio = False

                            if config['divisa'] == Tienda.Divisas.USD:
                                if producto.precio_divisa != precio_excel:
                                    hubo_cambio = True
                                    messages.info(request, mark_safe(f'ℹ️ Producto <strong>{producto.nombre}</strong>: Precio en USD actualizado → ${precio_excel}'))
                            else:
                                if producto.precio != precio_excel:
                                    hubo_cambio = True
                                    messages.info(request, mark_safe(f'ℹ️ Producto <strong>{producto.nombre}</strong>: Precio en ARS actualizado → ${precio_excel}'))

                            if producto.descuento != descuento_excel:
                                hubo_cambio = True
                                messages.info(request, mark_safe(f'ℹ️ Producto <strong>{producto.nombre}</strong>: Descuento actualizado → %{descuento_excel}'))

                            if hubo_cambio:
                                producto.precio_divisa = precio_excel
                                producto.descuento = descuento_excel
                                if not producto.sku:
                                    producto.sku = sku
                                producto.save()

                        if 'Atributos' in fila and isinstance(fila['Atributos'], str):
                            atributos = fila['Atributos'].split(';')
                            for atributo in atributos:
                                if ':' in atributo:
                                    nombre, valor = atributo.split(':', 1)
                                    nombre = nombre.strip()
                                    valor = valor.strip()
                                    if nombre and valor:
                                        Atributo.objects.get_or_create(producto=producto, nombre=nombre, valor=valor)

                        if 'Etiquetas' in fila and isinstance(fila['Etiquetas'], str):
                            etiquetas = fila['Etiquetas'].split(';')
                            for nombre_etiqueta in etiquetas:
                                nombre_etiqueta = nombre_etiqueta.strip()
                                if nombre_etiqueta:
                                    etiqueta, _ = Etiquetas.objects.get_or_create(nombre=nombre_etiqueta)
                                    producto.etiquetas.add(etiqueta)

                    messages.success(request, f"Productos cargados correctamente. Se eliminaron {eliminados} productos.")
                    return redirect('core:cargar_excel')

                except Exception as e:
                    messages.error(request, f"Ocurrió un error al procesar el archivo: {e}")
                    return redirect('core:cargar_excel')
    
        dolar = DolarActualizar(request.POST)
        if dolar.is_valid():
            if dolar.cleaned_data['dolar'] is None:
                return redirect('core:cargar_excel')
            valor_dolar = dolar.cleaned_data['dolar']
            config = Tienda.objects.first()
            if not config:
                config = Tienda.objects.create()
            config.valor_dolar = valor_dolar
            config.save()
            messages.success(request, f"Valor del Dolar actualizado a ${valor_dolar}")
    else:
        config = get_configuracion_tienda()
        excel = ExcelUploadForm()
        dolar = DolarActualizar(initial={'dolar': config['valor_dolar']})

    return render(request, 'core/cargar_excel.html', {'excel': excel,'dolar': dolar})
