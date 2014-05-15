from django.conf.urls import patterns
from django.conf.urls import url

from campus.views import BusRoutePolyView

from campus.views import RegionalCampusListView
import settings

urlpatterns = patterns('campus.views',
    url(r'^$', 'home', { 'points' : True }, name='home'),
    url(r'^locations/$', 'locations', name='locations'),
    url(r'^locations/(?P<loc>[\w-]+)/([^/]+/)??$', 'location', name='location'),
    url(r'^illustrated/$', 'home', name='illustrated'),
    url(r'^sidewalks/$', 'sidewalks', name='sidewalks'),
    url(r'^bikeracks/$', 'bikeracks', name='bikeracks'),
    url(r'^emergency-phones/$', 'emergency_phones', name='emergency_phones'),
    url(r'^parking/$', 'parking', name='parking'),
    url(r'^food/$', 'dining', name='dining'),
    url(r'^regional-campuses/((?P<campus>[\w-]+)/)?$', RegionalCampusListView.as_view(), name='regional'),
    url(r'^bus/routes/$', 'bus_routes', name='bus_routes'),
    url(r'^bus/(?P<route_id>\d+)/stops/$', 'bus_stops', name='bus_route_stops'),
    url(r'^bus/(?P<route_id>\d+)/poly/$', BusRoutePolyView.as_view(), name='bus_route_poly'),
    url(r'^bus/(?P<route_id>\d+)/gps/$', 'bus_gps', name='bus_gps'),

    url(r'^widget/$', 'widget', name='widget'),

    # campus admin views
    url(r'^admin/dump/', 'data_dump', name='dump_data'),

)
