from django.conf.urls.defaults import *

urlpatterns = patterns('example.views',
	url(r'^$', 'example_view', name="example"),
)