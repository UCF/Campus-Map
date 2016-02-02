from django import template
from re import sub

register = template.Library()

@register.filter(name='only_nums')
def allow_only_ints(value):
    return sub('[^\d]', '', value)
