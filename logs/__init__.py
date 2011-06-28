import logging
from django.conf import settings

class RequiredDebugFalse(logging.Filter):
	'''Only allow logging if DEBUG is FALSE'''
	def filter(self, record):
		if settings.DEBUG:
			return False
		return True
		
class RequiredDebugTrue(logging.Filter):
	'''Only allow logging if DEBUG is TRUE'''
	def filter(self, record):
		if settings.DEBUG:
			return True
		return False