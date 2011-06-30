from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = []

if settings.DEBUG:
	urlpatterns = patterns('',
		(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:],
			'django.views.static.serve',
			{
				'document_root': settings.MEDIA_ROOT,
				'show_indexes' : True,
			}
		),
	)

urlpatterns += patterns('',

	url(r'^(?P<url>.+)\.(.+)?', 'views.api'),

	(r'^', include('campus.urls')),
	#url(r'^$', direct_to_template, {'template':'base.djt'}, name='home'),
	(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/media/images/favicon.ico'}),
	(r'^robots.txt$', direct_to_template, {'template':'robots.txt', 'mimetype':'text/plain'}),
	
	# django-tinymce
	(r'^tinymce/', include('tinymce.urls')),
	
	# search
	url(r'^search/?$', 'views.search', name="search"),
	
	# org individual page and org profile pages
	url(r'^organizations/?$', 'views.organizations', name="organizations"),
	url(r'^organizations/(?P<id>\d+)/([^/]+/)?$', 'views.organization', name="org"),
	
	# admin
	(r'^admin/', include(admin.site.urls)),
	
	# catch-all for individual pages
	url(r'^(?P<page>[\w-]+)/$', 'views.pages', name="page"),
)

handler404 = 'views.page_not_found'
handler500 = 'views.server_error'