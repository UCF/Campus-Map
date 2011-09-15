from django.conf import settings
from time import time
from django.core.urlresolvers import reverse

def map_context(request):
	context_extras = {}
	
	# {{map_version}}
	if settings.DEBUG:
		context_extras['map_version'] = str(time())
	else:
		context_extras['map_version'] = settings.MAP_VERSION
	
	# {{base_url}}
	base_url = request.build_absolute_uri(reverse('home'))[:-1]
	context_extras['base_url'] = base_url
	
	# {{static}}
	context_extras['static'] = base_url + settings.MEDIA_URL
	
	return context_extras

class DisableCSRF(object):
	''' sad panda '''
	def process_view(self, request, callback, callback_args, callback_kwargs):
		setattr(request, '_dont_enforce_csrf_checks', True)