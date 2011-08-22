'''
	Check a series of URLs and make sure we get a response
	
'''
from django.core.management.base import BaseCommand
import urllib2
class Command(BaseCommand):
	def handle(self, *args, **options):
		
		if len(args):
			try:
				urllib2.urlopen(args[0])
				base = args[0]
			except ValueError:
				base = "http://%s/" % args[0]
		else:
			print "No host given, using 'my.mac'"
			base = "http://my.mac/"
		
		url_strings = [
			'',
			'search/',
			'organizations/',
			'locations/',
			'printable/',
			'locations/1/millican-hall/?org=354',
			'.json',
			'search/.json?q=commons',
			'locations/.json',
			"locations/52/.json",
			"parking/.kml?v=17",
			"locations/.kml?v=17",
			"sidewalks/.kml?v=17",
			"bikeracks/.json",
			"emergency-phones/.json",
		]
		
		for u in url_strings:
			try:
				url = base+u
				page = urllib2.urlopen(url)
				print "%-60s OK" % url
			except urllib2.URLError, e:
				print "%-60s Fail: %s" % (url, e)
			

