from django import template

register = template.Library()

@register.filter
def formato_pesos(value):
    try:
        valor_entero = int(float(value))
        if valor_entero == 0:
            return f"$0.00"
        return f"${valor_entero:,}".replace(",", ".")
    except (ValueError, TypeError):
        return value