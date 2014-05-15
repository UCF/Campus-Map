import re
import logging

from django.conf import settings
from django.core.urlresolvers import reverse, resolve, Resolver404
from django.http import HttpResponse, HttpRequest, HttpResponseNotFound, HttpResponseServerError
from django.views.generic import View

log = logging.getLogger(__name__)

formats = {
    'json' : {
        'mimetype' : 'application/json',
        'content'  : '{"error":"%s"}',
        },
    'txt'  : {
        'mimetype' : 'text/plain; charset=utf-8',
        'content'  : '%s',
        },
    'kml'  : {
        'mimetype' : 'application/vnd.google-earth.kml+xml',
        'content'  : '<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>%s</name></Document></kml>',
        },
    'xml'  : {
        'mimetype' : 'text/xml',
        'content'  : '<?xml version="1.0"?><error>%s</error>',
        },
    'bxml' : {
        'mimetype' : 'application/xml',
        'content'  : '<?xml version="1.0"?><error>%s</error>',
        },
    'ajax' : {
        'mimetype' : 'text/html; charset=utf-8',
        'content'  : '%s',
        },
}


class HttpResponseNotImplemented(HttpResponse):
    status_code = 501


def MonkeyPatchHttpRequest():
    '''
    Define is_<format> methods on the request object (called in base __init__.py)
    '''
    for format, o in formats.items():
        code = """def is_%s(self):
                    import re
                    return False if re.search('\.%s$', self.path) is None else True""" % (format, format)
        scope = {}
        exec code in scope
        setattr(HttpRequest, 'is_%s' % format, scope['is_%s' % format])


class MapMiddleware(object):

    def process_response(self, request, response):
        '''
        Cross-domain XHR using the html5 postMessage API.
        Not using Access Control anywhere in map, so only implementing here and not also in process_request
        '''
        response['Access-Control-Allow-Origin']  = '*'
        response['Access-Control-Allow-Methods'] = ','.join( ['GET', 'OPTIONS'] )


        '''
        Make sure reponses have right mime type and return Not Implemented server error when appropriate
        '''
        for format,spec in formats.items():
            is_api_call = getattr(request, 'is_%s' % format)
            if is_api_call():
                # view returned bad content type, assuming not implemented
                if response['Content-type'] != spec['mimetype']:
                    if response.status_code == 200:
                        rsp = dict(spec)
                        rsp['content'] = spec['content'] % 'Not Implemented'
                        return HttpResponseNotImplemented(**rsp)
                    elif response.status_code == 404:
                        rsp = dict(spec)
                        rsp['content'] = spec['content'] % 'Not Found'
                        return HttpResponseNotFound(**rsp)
                    elif response.status_code == 500:
                        if settings.DEBUG: return response
                        rsp = dict(spec)
                        rsp['content'] = spec['content'] % 'Server Error. Bummer'
                        return HttpResponseServerError(**rsp)
                    else:
                        msg = spec['content'] % ('Error %s' % response.status_code)
                        response['Content-Type'] = spec['mimetype']
                        response._container = [msg]

        return response


def handle_request(request, url):
    '''
    API view for detecting format without dirtying the urls file
    '''
    try:
        view, args, kwargs = resolve('/' + url)
    except Resolver404:
        view, args, kwargs = resolve('/' + url + '/')

    kwargs['request'] = request
    return view(*args, **kwargs)
