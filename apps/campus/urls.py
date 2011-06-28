from django.conf.urls.defaults import *
import settings

urlpatterns = patterns('campus.views',
	url(r'^(\.(?P<format>json|txt))?$', 'home', { 'points' : True }, name="home"),
	url(r'^locations/(\.(?P<format>json|kml))?$', 'locations', name="locations"),
	url(r'^locations/(?P<loc>[\w-]+)/([^/]+/)?(\.(?P<format>json|bubble))?$', 'location', name="location"),
	url(r'^sidewalks/(\.(?P<format>json|kml|txt))?$', 'sidewalks', name="sidewalks"),
	url(r'^bikeracks/(\.(?P<format>json|txt))?$', 'bikeracks', name="bikeracks"),
	url(r'^emergency-phones/(\.(?P<format>json|txt))?$', 'emergency_phones', name="emergency_phones"),
	url(r'^parking/(\.(?P<format>json|kml|txt))?$', 'parking', name="parking"),
	url(r'^regional-campuses/((?P<campus>[\w-]+)/)?(\.(?P<format>json))?$', 'regional_campuses', name="regional"),
	
	# Backward compatibiilty will old campus map URL structure
	# Example: http://campusmap.ucf.edu/flash/index.php?select=b_8118
	url(r'^flash/index\.php', 'backward_location'),
)
