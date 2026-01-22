from django.urls import path
from django.contrib import admin
from django.urls import path, include
from django.conf import settings

def response_404(request, *args, **kwargs):
    from django.http import Http404
    raise Http404("Esta sección solo está disponible dentro de una tienda.")

dummy_patterns_core = ([
    path('url1',response_404,name="toggle_mantenimiento")
], 'core')

dummy_patterns_admin = ([
    path('', response_404, name='index'),
    path('login/', response_404, name='login'),
    path('logout/', response_404, name='logout'),
    path('url2',response_404,name="customers_client_changelist"),
    path('url3',response_404,name="customers_domain_changelist"),
    path('url4/<int:pk>',response_404,name="core_tienda_change"),
    path('url5',response_404,name="core_eventospromociones_changelist"),
    path('url6',response_404,name="payment_cupon_changelist"),
    path('url7',response_404,name="payment_venta_changelist"),
    path('url8',response_404,name="products_producto_changelist"),
    path('url9',response_404,name="products_proveedor_changelist"),
    path('url10',response_404,name="products_ingresostock_changelist"),
    path('url11',response_404,name="products_lotestock_changelist"),
    path('url12',response_404,name="products_movimientostock_changelist"),
    path('url13',response_404,name="products_ajustestock_changelist"),
    path('url14',response_404,name="products_categoria_changelist"),
    path('url15',response_404,name="products_subcategoria_changelist"),
    path('url16',response_404,name="products_marca_changelist"),
    path('url17',response_404,name="products_etiquetas_changelist"),
    path('url18',response_404,name="products_tokenreseña_changelist"),
    path('url19',response_404,name="core_homesection_changelist"),
    path('url20',response_404,name="core_datosbancarios_changelist"),
    path('url21',response_404,name="core_mercadopagoconfig_changelist"),
], 'admin')


urlpatterns = [
    path('_admin/', include(dummy_patterns_admin)),
    path('_dummy_core/', include(dummy_patterns_core)),
    path('', include('website.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]