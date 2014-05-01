from django.conf.urls import *
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView
from django.views.generic import TemplateView

from api import formats
import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = []

urlpatterns += patterns('',

    # Backward compatibiilty will old campus map URL structure
    # Example: http://campusmap.ucf.edu/flash/index.php?select=b_8118
    url(r'^flash/index\.php', 'campus.views.backward_location'),
    ('^printmap', RedirectView.as_view(url='/printable/')),
    ('^address\.php', RedirectView.as_view(url='/directions/')),

    # Be careful. Because of the string replace, this is no longer a raw string
    url('^(?P<url>.*)\.(%s)' % '|'.join(formats), 'api.handle_request'),

    (r'^', include('campus.urls')),
    (r'^favicon\.ico$', RedirectView.as_view(url='%simages/favicon.ico' % settings.STATIC_URL)),

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

urlpatterns += staticfiles_urlpatterns()

handler404 = 'views.page_not_found'
handler500 = 'views.server_error'
