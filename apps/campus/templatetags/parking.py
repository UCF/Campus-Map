from django import template
from django.conf import settings
from django.utils.html import mark_safe

register = template.Library()

def permits(*args):
    from campus.models import parking_permit_colors

    text = {
        "D Permits"       : {'color': 'green',  'label': '&ldquo;D&rdquo; (Students/Visitors)'},
        "Events Garage"   : {'color': 'brown',  'label': 'Events Garage'},
        "B Permits"       : {'color': 'red',    'label': '&ldquo;B&rdquo; (Faculty)'},
        "C Permits"       : {'color': 'blue',   'label': '&ldquo;C&rdquo; (Staff)'},
        "Housing Permits" : {'color': 'orange', 'label': '&ldquo;R&rdquo; (Residents)'},
        "Towers"          : {'color': 'purple', 'label': 'Towers'}
    }

    retval = '<thead><tr><th>Permit Color</th><th>Permit Type</th></tr></thead>'
    for permit,color in parking_permit_colors.items():
        style = "background:%s; background:rgba(%s,%s,%s,.5); border:1px solid #%s;" % (
            color, int(color[0:2],16), int(color[2:4],16), int(color[4:],16), color )
        retval += '<tr><td><div class="permit" style="%s">%s</div></td><td>%s</td>' % (
                style, text[permit]['color'], text[permit]['label'] )

    retval += '<tr><td><img src="%simages/markers/handicap.png" alt="disabled icon"></td><td>Disabled Parking</td></tr>' % settings.STATIC_URL
    retval = '<table>%s</table>' % retval
    return mark_safe(retval)
register.simple_tag(permits)
