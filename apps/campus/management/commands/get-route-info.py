import campus
import settings

from campus.models import *

from campus.shuttle import ShuttleRouteAPI

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        client = ShuttleRouteAPI(settings.SHUTTLE_WSDL,
                                 settings.SHUTTLE_APP_CODE,
                                 settings.SHUTTLE_COST_CENTER_ID)

        shuttle_routes = client.get_routes()

        for route_id, route in shuttle_routes.iteritems():
            ex_route = ShuttleRoute.objects.filter(id=route_id)
            if len(ex_route) > 0:
                ex_route = ex_route[0]
                ex_route.shortname = route.shortname
                ex_route.color = route.color
                ex_route.description = route.description
                ex_route.save()
                route = ex_route
            else:
                n_route = ShuttleRoute()
                n_route.id = route.id
                n_route.shortname = route.shortname
                n_route.color = route.color
                n_route.description = route.description
                n_route.category = self.get_category(route.category)
                n_route.save()
                route = n_route

            shuttle_stops = client.get_route_stops(route.id)

            for stop in shuttle_stops:
                ex_stop = ShuttleStop.objects.filter(id=stop.id)
                if len(ex_stop) > 0:
                    self.update_stop(ex_stop[0], stop, route)
                else:
                    self.create_stop(stop, route)

    def get_category(self, cat_name):
        category = ShuttleCategory.objects.filter(name=cat_name)
        if len(category) > 0:
            return category[0]
        else:
            category = ShuttleCategory(name=cat_name)
            category.save()
            return category

    def update_stop(self, existing_stop, stop_info, route):
        existing_stop.name = stop_info.name
        existing_stop.lon = stop_info.point.lon
        existing_stop.lat = stop_info.point.lat
        existing_stop.route = route
        existing_stop.save()

    def create_stop(self, stop_info, route):
        new_stop = ShuttleStop()
        new_stop.id = stop_info.id
        new_stop.name = stop_info.name
        new_stop.lon = stop_info.point.lon
        new_stop.lat = stop_info.point.lat
        new_stop.route = route
        new_stop.save()
