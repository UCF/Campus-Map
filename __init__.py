import re
from django.http import HttpRequest
from django.conf import settings

# Define is_<format> methods on the HttpRequest class
for format in settings.FORMATS:
	code = """def is_%s(self): 
				import re 
				return False if re.search('\.%s$', self.path) is None else True""" % (format, format)
	scope = {}
	exec code in scope
	setattr(HttpRequest, 'is_%s' % format, scope['is_%s' % format])
