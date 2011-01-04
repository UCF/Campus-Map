from django.conf.urls.defaults import *
import settings


urlpatterns = patterns('campus.views',
	url(r'^$', 'home', name="home"),
	url(r'^buildings/.?(?P<format>json|kml)?$', 'home', name="buildings"),
)