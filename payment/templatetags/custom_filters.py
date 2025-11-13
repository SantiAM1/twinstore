from django import template
from django.core import signing
from django.utils.timesince import timesince
from django.utils import timezone

register = template.Library()

@register.filter
def formato_pesos(value):
    """
    Formatea un valor numérico a pesos Argentinos(ARS).

    Ejemplo:
        1000       -> $1.000
        1000.5     -> $1.000,50
        1000.567   -> $1.000,57
        0          -> $0.00
    """
    try:
        valor = float(value)
        entero = int(valor)
        if entero == 0:
            return "$0.00"
        decimales = round(valor - entero, 2)

        if decimales == 0:
            return f"${entero:,}".replace(",", ".")
        else:
            return f"${valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    except (ValueError, TypeError):
        return value

@register.filter
def absolute_url(relative_url, request):
    try:
        return request.build_absolute_uri(relative_url)
    except:
        return relative_url

@register.filter
def signing_data(input):
    """Firma un dato para evitar manipulaciones en el cliente."""
    return signing.dumps(input)

@register.filter
def imp_nac(value):
    """Calcula el importe neto de un valor SIN IVA incluido (21%)."""
    valor = float(value)
    return valor/1.21

@register.filter
def sub(value, arg):
    return float(value) - float(arg)

@register.filter
def timesince_simple(value):
    """Devuelve el tiempo transcurrido desde 'value' hasta ahora en un formato simple."""
    if not value:
        return ""
    result = timesince(value, timezone.now())
    primera_parte = result.split(",")[0]
    return f"{primera_parte}"

@register.filter
def mul(value, arg):
    """Multiplica dos valores numéricos."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''