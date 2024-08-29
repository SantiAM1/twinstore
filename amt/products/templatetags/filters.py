from urllib.parse import urlencode, parse_qs, urlsplit, urlunsplit
from django import template
import logging

register = template.Library()

@register.filter
def add_to_query(url, new_param):
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string, keep_blank_values=True)

    key, value = new_param.split(',', 1)  # Asegurarse de dividir en máximo dos partes
    # Eliminar los espacios en blanco que podrían causar problemas de comparación
    normalized_value = value.strip()

    # Convertir la lista de valores en un conjunto para asegurar la unicidad
    if key in query_params:
        existing_values = set(query_params[key])
    else:
        existing_values = set()

    # Añadir el valor si no está presente en el conjunto
    if normalized_value not in existing_values:
        existing_values.add(normalized_value)
        query_params[key] = list(existing_values)  # Convertir de nuevo a lista para urlencode

    # Reconstruir la cadena de consulta
    new_query_string = urlencode(query_params, doseq=True)
    return urlunsplit((scheme, netloc, path, new_query_string, fragment))



@register.filter
def remove_from_query(url, args):
    key, value = args.split(',')
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string, keep_blank_values=True)
    if key in query_params and value in query_params[key]:
        query_params[key].remove(value)
        if not query_params[key]:
            del query_params[key]

    new_query_string = urlencode(query_params, doseq=True)
    return urlunsplit((scheme, netloc, path, new_query_string, fragment))
