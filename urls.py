from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template, redirect_to
import settings
from api import formats

from django.contrib import admin
admin.autodiscover()

urlpatterns = []

if settings.DEBUG or settings.SERVE_STATIC_FILES:
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
	
	# Backward compatibiilty will old campus map URL structure
	# Example: http://campusmap.ucf.edu/flash/index.php?select=b_8118
	url(r'^flash/index\.php', 'campus.views.backward_location'),
	('^printmap', redirect_to, {'url': '/printable/'}),
	('^address\.php', redirect_to, {'url': '/directions/'}),
	
	# Be careful. Because of the string replace, this is no longer a raw string
	url('^(?P<url>.*)\.(%s)' % '|'.join(formats), 'api.handle_request'),

	(r'^', include('campus.urls')),
	#url(r'^$', direct_to_template, {'template':'base.djt'}, name='home'),
	(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '%simages/favicon.ico' % settings.MEDIA_URL}),
	(r'^robots.txt$', direct_to_template, {'template':'robots.txt', 'mimetype':'text/plain'}),
	
	# django-tinymce
	(r'^tinymce/', include('tinymce.urls')),
	
	# search
	url(r'^search/$', 'views.search', name="search"),
	
	# print layout
	url(r'^print/$', 'views.print_layout', name="print"),
	
	# org individual page and org profile pages
	url(r'^organizations/$', 'views.organizations', name="organizations"),
	url(r'^organizations/(?P<id>\d+)/([^/]+/)?$', 'views.organization', name="org"),
	
	# admin
	url(r'^admin/password_reset/$', 'django.contrib.auth.views.password_reset', name='password_reset'),
	(r'^password_reset/done/$', 'django.contrib.auth.views.password_reset_done'),
	(r'^reset/(?P<uidb36>[-\w]+)/(?P<token>[-\w]+)/$', 'django.contrib.auth.views.password_reset_confirm'),
	(r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete'),
	(r'^admin/', include(admin.site.urls)),
	
	# catch-all for individual pages
	url(r'^(?P<page>[\w-]+)/$', 'views.pages', name="page"),
)

handler404 = 'views.page_not_found'
handler500 = 'views.server_error'