from django.conf.urls.defaults import *
import settings


urlpatterns = patterns('campus.views',
	url(r'^$', 'home', name="home"),
)