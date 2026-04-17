from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.http import Http404

def response_404(request, *args, **kwargs):
    raise Http404("Esta sección solo está disponible dentro de una tienda.")

dummy_patterns_core = ([
    path('dummy-mantenimiento/', response_404, name="toggle_mantenimiento")
], 'core')

# 1. LIMPIEZA: Sacamos index, login, logout, client y domain.
# Esos los va a manejar el admin REAL para que puedas entrar y crear tiendas.
dummies_para_unfold = [
    path('dummy/tienda/<int:pk>/', response_404, name="core_tienda_change"),
    path('dummy/eventos/', response_404, name="core_eventospromociones_changelist"),
    path('dummy/cupones/', response_404, name="payment_cupon_changelist"),
    path('dummy/ventas/', response_404, name="payment_venta_changelist"),
    path('dummy/productos/', response_404, name="products_producto_changelist"),
    path('dummy/proveedores/', response_404, name="products_proveedor_changelist"),
    path('dummy/ingreso/', response_404, name="products_ingresostock_changelist"),
    path('dummy/lote/', response_404, name="products_lotestock_changelist"),
    path('dummy/movimiento/', response_404, name="products_movimientostock_changelist"),
    path('dummy/ajuste/', response_404, name="products_ajustestock_changelist"),
    path('dummy/categorias/', response_404, name="products_categoria_changelist"),
    path('dummy/subcategorias/', response_404, name="products_subcategoria_changelist"),
    path('dummy/marcas/', response_404, name="products_marca_changelist"),
    path('dummy/etiquetas/', response_404, name="products_etiquetas_changelist"),
    path('dummy/tokenresena/', response_404, name="products_tokenreseña_changelist"),
    path('dummy/home/', response_404, name="core_homesection_changelist"),
    path('dummy/banco/<int:pk>/', response_404, name="core_datosbancarios_change"),
    path('dummy/mercadopago/<int:pk>/', response_404, name="core_mercadopagoconfig_change"),
    path('dummy/shipping/', response_404, name="shipping_shippingconfig_changelist"),
]

# 2. EL TRUCO DE MAGIA: Fusionamos las URLs
# Extraemos las rutas reales del admin de Django
original_urls, app_name, namespace = admin.site.urls

# Sumamos nuestras rutas de mentira a las rutas reales en una sola lista
custom_admin_urls = dummies_para_unfold + original_urls

urlpatterns = [
    # 3. Inyectamos TODAS las rutas bajo la misma URL '/admin/'
    path('admin/', (custom_admin_urls, app_name, namespace)),
    
    path('_dummy_core/', include(dummy_patterns_core)),
    path('', include('website.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]