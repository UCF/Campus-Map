from django.conf import settings
from django.conf.urls import patterns
from django.conf.urls import url
from django.views.generic import RedirectView

urlpatterns = patterns('campus.views',
    url(r'^$', 'home', { 'points' : True }, name='home'),
    url(r'^locations/$', 'locations', name='locations'),
    url(r'^locations/(?P<loc>[\w-]+)/([^/]+/)??$', 'location', name='location'),
    url(r'^illustrated/$', 'home', name='illustrated'),
    url(r'^sidewalks/$', 'sidewalks', name='sidewalks'),
    url(r'^bikeracks/$', 'bikeracks', name='bikeracks'),
    url(r'^charging-stations', 'electric_charging_stations', name='electric_charging_stations'),
    url(r'^emergency-phones/$', 'emergency_phones', name='emergency_phones'),
    url(r'^phones/$', RedirectView.as_view(pattern_name='emergency_phones')),
    url(r'^emergency-aeds/$', 'emergency_aeds', name='emergency_aeds'),
    url(r'^emergency/$', 'emergency_all', name='emergency_all'),
    url(r'^aeds/$', RedirectView.as_view(pattern_name='emergency_aeds')),
    url(r'^parking/$', 'parking', name='parking'),
    url(r'^food/$', 'dining', name='dining'),
    url(r'^regional-campuses/((?P<campus>[\w-]+)/)?$', 'regional_campuses', name='regional'),
    url(r'^shuttles/$', 'shuttles', name='shuttles'),
    url(r'^weather/$', 'weather', name='weather'),

    url(r'^widget/$', 'widget', name='widget'),

    # campus admin views
    url(r'^admin/dump/', 'data_dump', name='dump_data'),

)
