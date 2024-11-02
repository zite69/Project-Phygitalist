from django.template.defaultfilters import register
from urllib.parse import unquote as unquote_method #python3

@register.filter
def unquote(value):
    return unquote_method(value)
