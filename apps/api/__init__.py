import re
import logging

import types

from django.conf import settings
from django.urls import reverse, resolve, Resolver404
from django.http import HttpResponse, HttpRequest, HttpResponseNotFound, HttpResponseServerError
from django.views.generic import View

log = logging.getLogger(__name__)

formats = {
    'json': {
        'content_type': 'application/json',
        'content': '{"error":"%s"}',
        },
    'txt': {
        'content_type': 'text/plain; charset=utf-8',
        'content': '%s',
        },
    'kml': {
        'content_type': 'application/vnd.google-earth.kml+xml',
        'content': '<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>%s</name></Document></kml>',
        },
    'xml': {
        'content_type': 'text/xml',
        'content': '<?xml version="1.0"?><error>%s</error>',
        },
    'bxml': {
        'content_type': 'application/xml',
        'content': '<?xml version="1.0"?><error>%s</error>',
        },
    'ajax': {
        'content_type': 'text/html; charset=utf-8',
        'content': '%s',
        },
}


class HttpResponseNotImplemented(HttpResponse):
    status_code = 501


class MonkeyPatchHttpRequest():
    '''
    Define is_<format> methods on the request object (called in base __init__.py)
    '''

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.is_bxml = types.MethodType(is_bxml, request)
        request.is_kml = types.MethodType(is_kml, request)
        request.is_json = types.MethodType(is_json, request)
        request.is_txt = types.MethodType(is_txt, request)
        request.is_xml = types.MethodType(is_xml, request)

        return self.get_response(request)

def is_bxml(self):
    return False if re.search('\.bxml$', self.path) is None else True

def is_kml(self):
    return False if re.search('\.kml$', self.path) is None else True

def is_json(self):
    return False if re.search('\.json$', self.path) is None else True

def is_txt(self):
    return False if re.search('\.txt$', self.path) is None else True

def is_xml(self):
    return False if re.search('\.xml$', self.path) is None else True

class MapMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        '''
        Cross-domain XHR using the html5 postMessage API.
        Not using Access Control anywhere in map, so only implementing here and not also in process_request
        '''
        response['Access-Control-Allow-Origin']  = '*'
        response['Access-Control-Allow-Methods'] = ','.join( ['GET', 'OPTIONS'] )

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
