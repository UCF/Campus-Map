from django.conf.urls.defaults import *
import settings

urlpatterns = patterns('campus.views',
	url(r'^(\.(?P<format>json|kml))?$', 'home', { 'points' : True }, name="home"),
	url(r'^buildings/(\.(?P<format>json|kml))?$', 'buildings', name="buildings"),
	url(r'^organizations/(\.(?P<format>json))?$', 'organizations', name="organizations"),
	url(r'^search/(\.(?P<format>json|list))?$', 'search', name="search"),
	url(r'^location/(?P<loc>\w+)/([^/]+/)?(\.(?P<format>json|bubble))?$', 'location', name="location"),
)
