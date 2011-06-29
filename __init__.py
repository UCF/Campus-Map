import re
from django.http import HttpRequest

class RequestAPIFormatMixin():
	'''Mixin to provide detection for format type here instead of in URLs'''
	
	def is_json(self):
		return False if re.search('\.json$', self.path) is None else True
	
	def is_txt(self):
		return False if re.search('\.txt$', self.path) is None else True
	
	def is_xml(self):
		return False if re.search('\.xml$', self.path) is None else True
	
	def is_bxml(self):
		return False if re.search('\.bxml$', self.path) is None else True
		
	def is_kml(self):
		return False if re.search('\.kxml$', self.path) is None else True
	
	def is_bubble(self):
		return False if re.search('\.bubble$', self.path) is None else True
	
HttpRequest.__bases__ += (RequestAPIFormatMixin,)