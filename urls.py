from django.conf import settings
from django.conf.urls import *
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from django.contrib.auth.views import password_reset, password_reset_done, password_reset_confirm, password_reset_complete

from api import formats, handle_request
from campus import views as campus_views
import views
import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = []

urlpatterns += [
    # Backward compatibility will old campus map URL structure
    # Example: http://campusmap.ucf.edu/flash/index.php?select=b_8118
    url(r'^flash/index\.php', campus_views.backward_location),
    url(r'^printmap', RedirectView.as_view(url='/printable/')),
    url(r'^address\.php', RedirectView.as_view(url='/directions/')),

    # Be careful. Because of the string replace, this is no longer a raw string
    url(r'^(?P<url>.*)\.(%s)' % '|'.join(formats), handle_request),

    url(r'^', include('campus.urls')),

    # django-tinymce
    url(r'^tinymce/', include('tinymce.urls')),

    # search
    url(r'^search/$', views.search, name="search"),

    # print layout
    url(r'^print/$', views.print_layout, name="print"),

    # org individual page and org profile pages
    url(r'^organizations/$', views.organizations, name="organizations"),
    url(r'^organizations/(?P<id>\d+)/([^/]+/)?$', views.organization, name="org"),

    # admin
    url(r'^admin/password_reset/$', password_reset, name='password_reset'),
    url(r'^password_reset/done/$', password_reset_done, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[-\w]+)/(?P<token>[-\w]+)/$', password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done/$', password_reset_complete, name='password_reset_complete'),
    url(r'^admin/', include(admin.site.urls)),

    # catch-all for individual pages
    url(r'^(?P<page>[\w-]+)/$', views.pages, name="page"),
]

urlpatterns += staticfiles_urlpatterns()
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = views.page_not_found
handler500 = views.server_error
