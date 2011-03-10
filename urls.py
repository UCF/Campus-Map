from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	(r'^', include('campus.urls')),
	#url(r'^$', direct_to_template, {'template':'base.djt'}, name='home'),
	(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/media/images/favicon.ico'}),
	(r'^robots.txt$', direct_to_template, {'template':'robots.txt', 'mimetype':'text/plain'}),
	(r'^admin/', include(admin.site.urls)),
	url(r'^(?P<page>[a-z]+)/(\.(?P<format>json|txt))?$', 'views.pages', name="page"),
)

if settings.DEBUG:
	urlpatterns += patterns('',
		(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:],
			'django.views.static.serve',
			{
				'document_root': settings.MEDIA_ROOT,
				'show_indexes' : True,
			}
		),
	)