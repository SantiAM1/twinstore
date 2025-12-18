from django.urls import path
from .views import (
    home,
    politicas_priv,
    politicas_devolucion,
    politicas_envios,
    preguntas_frecuentes,
    terminos_condiciones,
    boton_arrepentimiento,
    politicas_tecnico,
    contacto,
    BusquedaPredictivaView,
    cache_clear,
    test,
    toggle_mantenimiento
)

app_name = "core"

urlpatterns = [
    path('', home, name="home"),
    path('politicas-privacidad/',politicas_priv,name="politicas-privacidad"),
    path('politicas-devoluciones/',politicas_devolucion,name="politicas-devolucion"),
    path('politicas-envios/',politicas_envios,name="politicas-envios"),
    path('preguntas-frecuentes/',preguntas_frecuentes,name="faq"),
    path('terminos-condiciones/',terminos_condiciones,name="terminos-condiciones"),
    path('arrepentimiento/',boton_arrepentimiento,name="arrepentimiento"),
    path('politicas-tecnico/',politicas_tecnico,name="politicas-tecnico"),
    path('contacto/',contacto,name="contacto"),
    path('api/busqueda_predictiva/',BusquedaPredictivaView.as_view(), name='busqueda_predictiva'),
    path('cache_clear/',cache_clear,name="cache_clear"),
    path('test/',test,name="test"),
    path('toggle-mantenimiento/', toggle_mantenimiento, name='toggle_mantenimiento'),
]
