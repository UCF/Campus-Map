from django.conf.urls.defaults import *
import settings

urlpatterns = patterns('campus.views',
	url(r'^(\.(?P<format>json|txt))?$', 'home', { 'points' : True }, name="home"),
	url(r'^buildings/(\.(?P<format>json|kml))?$', 'buildings', name="buildings"),
	url(r'^search/(\.(?P<format>json|list))?$', 'search', name="search"),
	url(r'^location/(?P<loc>\w+)/([^/]+/)?(\.(?P<format>json|bubble))?$', 'location', name="location"),
)
