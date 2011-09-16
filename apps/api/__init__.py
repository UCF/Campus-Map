import re
from django.conf import settings
from django.core.urlresolvers import reverse, resolve
from django.http import HttpResponse, HttpRequest


formats = {
	'json' : {
		'mimetype' : 'application/json',
		'content'  : '{"error":"Not Implemented"}',
		},
	'txt'  : {
		'mimetype' : 'text/plain; charset=utf-8',
		'content'  : 'Not Implemented',
		},
	'kml'  : {
		'mimetype' : 'application/vnd.google-earth.kml+xml',
		'content'  : '<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"></kml>',
		},
	'xml'  : {
		'mimetype' : 'text/xml',
		'content'  : '<?xml version="1.0"?><error>Not Implemented</error>',
		},
	'bxml' : {
		'mimetype' : 'application/xml',
		'content'  : '<?xml version="1.0"?><error>Not Implemented</error>',
		},
	'ajax' : {
		'mimetype' : 'text/html',
		'content'  : 'Not Implemented',
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
		Make sure reponses have right mime type and return Not Implemented server error when appropriate
		'''
		for format,spec in formats.items():
			is_api_call = getattr(request, 'is_%s' % format)
			if is_api_call():
				if response['Content-type'] != spec['mimetype']:
					# view returned bad content type, assuming not implemented
					return HttpResponseNotImplemented(**spec)
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
