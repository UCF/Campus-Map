import re
import urllib

from django import template


def weather(json_request = False, text_request = False):
    '''
    Yahoo Weather
    '''
    try:
        response = requests.get(settings.WEATHER_URL,
                                timeout=settings.REQUEST_TIMEOUT).json()


        w_json = {"temperature": u'{0}\u00B0F'.format(response['tempN']), "description": response['condition']}
        w_text = u'temperature: {0}\u00B0F\ndescription: {1}'.format(response['tempN'], response['condition'])

        # grab just icon and description
        html = '<div class="navweatherimage"><img src="' + response['imgSmall'] + '" title="' + response['condition'] + '" alt="' + response['condition'] + '" ></div><div class="discription">' + response['temp'] + ', ' + response['condition'] + '<div class="floatright">'
    except Exception:
        return {'weather': None, 'error': 'IOError with opening URL'}

    if json_request:
        return w_json
    elif text_request:
        return w_text
    else:
        return {'weather': html}

register = template.Library()
register.inclusion_tag("templatetags/weather.html")(weather)
