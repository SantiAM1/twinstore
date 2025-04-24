from django.urls import path
from .views import home,local,cargar_productos_excel,buscar_productos,verificar_throttle,politicas_priv,politicas_devolicion,politicas_envios,preguntas_frecuentes,terminos_condiciones

app_name = "core"

urlpatterns = [
    path('', home, name="home"),
    path('local/', local, name="local"),
    path('cargar-productos/', cargar_productos_excel, name='cargar_excel'),
    path('api/buscar-productos/',buscar_productos,name="buscar_prod"),
    path('test/throttle-status/', verificar_throttle, name='verificar_throttle'),
    path('politicas-privacidad/',politicas_priv,name="politicas-privacidad"),
    path('politicas-devoluciones/',politicas_devolicion,name="politicas-devolucion"),
    path('politicas-envios/',politicas_envios,name="politicas-envios"),
    path('preguntas-frecuentes/',preguntas_frecuentes,name="faq"),
    path('terminos-condiciones/',terminos_condiciones,name="terminos-condiciones")
]
