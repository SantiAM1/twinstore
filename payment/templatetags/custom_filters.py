from django import template

register = template.Library()

@register.filter
def formato_pesos(value):
    try:
        valor = float(value)
        # Separamos parte entera y decimal
        entero = int(valor)
        if entero == 0:
            return "$0.00"
        decimales = round(valor - entero, 2)

        if decimales == 0:
            return f"${entero:,}".replace(",", ".")  # Sin decimales
        else:
            # Mostramos 2 decimales reales, con separador decimal
            return f"${valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    except (ValueError, TypeError):
        return value

@register.filter
def absolute_url(relative_url, request):
    try:
        return request.build_absolute_uri(relative_url)
    except:
        return relative_url  # fallback en caso de error