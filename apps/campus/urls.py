from django.conf import settings
from django.conf.urls import url
from django.views.generic import RedirectView

from campus import views

urlpatterns = [
    url(r'^$', views.home, { 'points' : True }, name='campus.views.home'),
    url(r'^locations/$', views.locations, name='campus.views.locations'),
    url(r'^locations/(?P<loc>[\w-]+)/([^/]+/)??$', views.location, name='campus.views.location'),
    url(r'^illustrated/$', views.home, name='campus.views.illustrated'),
    url(r'^sidewalks/$', views.sidewalks, name='campus.views.sidewalks'),
    url(r'^bikeracks/$', views.bikeracks, name='campus.views.bikeracks'),
    url(r'^charging-stations', views.electric_charging_stations, name='campus.views.electric_charging_stations'),
    url(r'^emergency-phones/$', views.emergency_phones, name='campus.views.emergency_phones'),
    url(r'^phones/$', RedirectView.as_view(pattern_name='campus.views.emergency_phones')),
    url(r'^emergency-aeds/$', views.emergency_aeds, name='campus.views.emergency_aeds'),
    url(r'^emergency/$', views.emergency_all, name='campus.views.emergency_all'),
    url(r'^aeds/$', RedirectView.as_view(pattern_name='campus.views.emergency_aeds')),
    url(r'^parking/$', views.parking, name='campus.views.parking'),
    url(r'^food/$', views.dining, name='campus.views.dining'),
    url(r'^regional-campuses/((?P<campus>[\w-]+)/)?$', views.regional_campuses, name='campus.views.regional'),
    url(r'^shuttles/$', views.shuttles, name='campus.views.shuttles'),
    url(r'^weather/$', views.weather, name='campus.views.weather'),

    url(r'^widget/$', views.widget, name='campus.views.widget'),

    # campus admin views
    url(r'^admin/dump/', views.data_dump, name='campus.views.dump_data')
]
