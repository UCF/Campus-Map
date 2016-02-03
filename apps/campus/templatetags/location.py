from django import template
from re import sub as replace

register = template.Library()


@register.filter(name='whitelist')
def whitelist(value):
    return replace('[^\da-zA-Z\-_]', '', value)
