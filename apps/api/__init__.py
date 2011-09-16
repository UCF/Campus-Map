import re
from django.conf import settings
from django.core.urlresolvers import reverse, resolve
from django.http import HttpResponse, HttpRequest

formats = {
	'json' : {
		'mime_type'       : 'application/json',
		'errror_response' : '',
		},
	'txt'  : {
		'mime_type'       : 'text/plain; charset=utf-8',
		'errror_response' : '',
		},
	'kml'  : {
		'mime_type'       : 'application/vnd.google-earth.kml+xml',
		'errror_response' : '',
		},
	'xml'  : {
		'mime_type'       : 'text/xml',
		'errror_response' : '',
		},
	'bxml' : {
		'mime_type'       : 'application/xml',
		'errror_response' : '',
		},
	'ajax' : {
		'mime_type'       : 'text/html',
		'errror_response' : '',
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
		for f,o in formats.items():
			is_api_call = getattr(request, 'is_%s' % f)
			if is_api_call():
				if response['Content-type'] is not formats[f
				print format, o
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
