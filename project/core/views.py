from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.safestring import mark_safe
import pandas as pd
import uuid
from .forms import ExcelUploadForm
from products.models import Producto, Marca, Categoria, SubCategoria, Atributo
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.cache import cache
import hashlib
from django.core.paginator import Paginator
# Create your views here.

def pagina_mantenimiento(request):
    return render(request, 'core/mantenimiento.html')

@require_GET
def buscar_productos(request):
    q = request.GET.get('q', '').strip().lower()
    if not q or len(q) < 2:
        return JsonResponse([], safe=False)

    hash_q = hashlib.md5(q.encode()).hexdigest()
    cache_key = f"autocomplete:{hash_q}"

    resultados = cache.get(cache_key)

    if not resultados:
        productos = Producto.objects.filter(nombre__icontains=q).values_list('nombre', flat=True)[:10]
        resultados = list(productos)
        cache.set(cache_key, resultados, 60 * 5)

    return JsonResponse(resultados, safe=False)

def home(request):
    productos_descuento = Producto.objects.filter(precio_anterior__isnull=False)[:20]
    return render(request,'core/inicio.html',{
        'productos_descuento': productos_descuento,
    })

def local(request):
    return render(request,'core/local.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def cargar_productos_excel(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.cleaned_data['archivo']
            try:
                df = pd.read_excel(archivo)

                if df.empty:
                    messages.error(request, "El archivo Excel está vacío.")
                    return redirect('cargar_excel')

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

                    producto, creado = Producto.objects.get_or_create(
                        nombre=fila['Producto'],
                        defaults={
                            'marca': marca,
                            'sub_categoria': sub_categoria,
                            'precio': fila['Precio'],
                            'descuento': fila['Descuento'],
                            'sku': sku
                        }
                    )
                    if creado:
                            messages.success(request, mark_safe(f'✅ Producto <strong>{producto.nombre}</strong> agregado'))
                    else:
                        if producto.precio != fila['Precio'] or producto.descuento != fila['Descuento']:
                            messages.info(request, mark_safe(f'ℹ️ Producto <strong>{producto.nombre}</strong> actualizado'))


                    if not creado:
                        producto.precio = fila['Precio']
                        producto.descuento = fila['Descuento']
                        if not producto.sku:
                            producto.sku = sku
                        producto.save()
                    
                    if 'Atributos' in fila and isinstance(fila['Atributos'], str):
                        atributos = fila['Atributos'].split('|')
                        for atributo in atributos:
                            nombre_valor = atributo.split(':')
                            if len(nombre_valor) == 2:
                                nombre = nombre_valor[0].strip()
                                valor = nombre_valor[1].strip()
                                Atributo.objects.get_or_create(producto=producto, nombre=nombre, valor=valor)

                messages.success(request, f"Productos cargados correctamente. Se eliminaron {eliminados} productos.")
                return redirect('core:cargar_excel')

            except Exception as e:
                messages.error(request, f"Ocurrió un error al procesar el archivo: {e}")
                return redirect('core:cargar_excel')
    else:
        form = ExcelUploadForm()

    return render(request, 'core/cargar_excel.html', {'form': form})

