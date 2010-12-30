from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

	# Example:
	# (r'^django_base/', include('django_base.foo.urls')),
	# url(r'^ajax/search$', 'foo.views.search', name="search"),
	
	# Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
	# to INSTALLED_APPS to enable admin documentation:
	# (r'^admin/doc/', include('django.contrib.admindocs.urls')),

	# Enable Admin
	(r'^admin/', include(admin.site.urls)),

	#(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
	#(r'^logout/$', 'django.contrib.auth.views.logout_then_login'),
	
	url(r'^$', direct_to_template, {'template':'base.djt'}, name='home'),
	(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/media/images/favicon.ico'}),
	(r'^robots.txt$', direct_to_template, {'template':'robots.txt', 'mimetype':'text/plain'}),
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