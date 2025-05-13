from django import template

register = template.Library()

@register.filter
def array_index(collection, index):
    try:
        return collection[index]
    except IndexError:
        return collection[0] if len(collection) > 0 else ""
