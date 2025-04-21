from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.safestring import mark_safe
import pandas as pd
import uuid
from .forms import ExcelUploadForm,DolarActualizar
from products.models import Producto, Marca, Categoria, SubCategoria, Atributo
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.cache import cache
import hashlib
from django.core.paginator import Paginator
from .decorators import bloquear_si_mantenimiento
from .throttling import PrediccionBusquedaThrottle
from rest_framework.decorators import throttle_classes
from .models import DolarConfiguracion

from django.contrib.admin.views.decorators import staff_member_required
from django.utils.timezone import now
from core.utils import obtener_valor_dolar
# Create your views here.

@staff_member_required
def verificar_throttle(request):
    # Simulamos usuarios o IPs de prueba (esto es solo demostrativo)
    ejemplos = [
        'throttle_user_1',  # Clave ejemplo para usuarios autenticados
        'throttle_anon_192.168.0.100',  # Clave ejemplo para IP
    ]

    data = []
    for clave in ejemplos:
        valor = cache.get(clave)
        if valor:
            data.append({'clave': clave, 'valor': valor})

    return render(request, 'core/throttle_panel.html', {
        'fecha': now(),
        'throttles': data,
    })

def pagina_mantenimiento(request):
    return render(request, 'core/mantenimiento.html')

@require_GET
@bloquear_si_mantenimiento
@throttle_classes([PrediccionBusquedaThrottle])
def buscar_productos(request):
    q = request.GET.get('q', '').strip().lower()
    if not q or len(q) < 2:
        return JsonResponse([], safe=False)

    hash_q = hashlib.md5(q.encode()).hexdigest()
    cache_key = f"autocomplete:{hash_q}"

    resultados = cache.get(cache_key)

    if not resultados:
        productos = Producto.objects.filter(nombre__icontains=q).values('nombre', 'slug')[:10]
        resultados = list(productos)
        cache.set(cache_key, resultados, 60 * 5)

    return JsonResponse(resultados, safe=False)

def home(request):
    productos_descuento = Producto.objects.filter(descuento__gt=0).order_by('-descuento')[:20]
    return render(request,'core/inicio.html',{
        'productos_descuento': productos_descuento,
    })

def local(request):
    return render(request,'core/local.html')

@login_required
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

                    nombres_en_excel = df['Producto'].tolist()
                    productos_existentes = Producto.objects.all()
                    productos_a_eliminar = productos_existentes.exclude(nombre__in=nombres_en_excel)
                    eliminados = productos_a_eliminar.count()

                    for eliminado in productos_a_eliminar:
                        messages.error(request, mark_safe(f'❌ Producto <strong>{eliminado.nombre}</strong> eliminado'))

                    productos_a_eliminar.delete()

                    for _, fila in df.iterrows():
                        marca, _ = Marca.objects.get_or_create(nombre=fila['Marca'])

                        try:
                            sub_categoria = SubCategoria.objects.get(nombre=fila['Sub-categoria'])
                            categoria = sub_categoria.categoria
                        except SubCategoria.DoesNotExist:
                            messages.warning(request, f'Subcategoría no encontrada: {fila["Sub-categoria"]}')
                            continue

                        sku = f"{marca.nombre[:3].upper()}-{sub_categoria.nombre[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"

                        valor_dolar = obtener_valor_dolar()
                        print(valor_dolar)

                        producto, creado = Producto.objects.get_or_create(
                            nombre=fila['Producto'],
                            defaults={
                                'marca': marca,
                                'sub_categoria': sub_categoria,
                                'precio_dolar': fila['Precio USD'],
                                'descuento': fila['Descuento'],
                                'sku': sku
                            }
                        )

                        if creado:
                            messages.success(request, mark_safe(f'✅ Producto <strong>{producto.nombre}</strong> agregado'))
                        else:
                            if not producto.slug:
                                producto.generar_slug()
                                producto.save()
                            precio_dolar_excel = fila['Precio USD']
                            descuento_excel = fila['Descuento']

                            hubo_cambio = False

                            if producto.precio_dolar != precio_dolar_excel:
                                hubo_cambio = True
                                messages.info(request, mark_safe(f'ℹ️ Producto <strong>{producto.nombre}</strong>: Precio en USD actualizado → ${precio_dolar_excel}'))

                            if producto.descuento != descuento_excel:
                                hubo_cambio = True
                                messages.info(request, mark_safe(f'ℹ️ Producto <strong>{producto.nombre}</strong>: Descuento actualizado → %{descuento_excel}'))

                            if hubo_cambio:
                                producto.precio_dolar = precio_dolar_excel
                                producto.descuento = descuento_excel
                                if not producto.sku:
                                    producto.sku = sku
                                producto.save()

                        # Eliminar atributos anteriores para no duplicar
                        producto.atributos.all().delete()

                        # Cargar nuevos atributos separados por ';'
                        if 'Atributos' in fila and isinstance(fila['Atributos'], str):
                            atributos = fila['Atributos'].split(';')
                            for atributo in atributos:
                                if ':' in atributo:
                                    nombre, valor = atributo.split(':', 1)
                                    nombre = nombre.strip()
                                    valor = valor.strip()
                                    if nombre and valor:
                                        Atributo.objects.get_or_create(producto=producto, nombre=nombre, valor=valor)

                    messages.success(request, f"Productos cargados correctamente. Se eliminaron {eliminados} productos.")
                    return redirect('core:cargar_excel')

                except Exception as e:
                    messages.error(request, f"Ocurrió un error al procesar el archivo: {e}")
                    return redirect('core:cargar_excel')
    
        dolar = DolarActualizar(request.POST)
        if dolar.is_valid():
            valor_dolar = dolar.cleaned_data['dolar']
            dolar_model = DolarConfiguracion.objects.first()
            dolar_model.valor = valor_dolar
            dolar_model.save()
            messages.success(request, f"Valor del Dolar actualizado a ${valor_dolar}")
    else:
        excel = ExcelUploadForm()
        dolar = DolarActualizar(initial={'dolar': obtener_valor_dolar()})

    return render(request, 'core/cargar_excel.html', {'excel': excel,'dolar': dolar})
