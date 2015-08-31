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

	def get_category(self, catName):
		category = ShuttleCategory.objects.filter(name=catName)
		if len(category) > 0:
			return category[0]
		else:
			category = ShuttleCategory(name=catName)
			category.save()
			return category

	def update_stop(self, existingStop, stopInfo, route):
		existingStop.name = stopInfo.name
		existingStop.lon = stopInfo.point.lon
		existingStop.lat = stopInfo.point.lat
		existingStop.route = route
		existingStop.save()

	def create_stop(self, stopInfo, route):
		newStop = ShuttleStop()
		newStop.id = stopInfo.id
		newStop.name = stopInfo.name
		newStop.lon = stopInfo.point.lon
		newStop.lat = stopInfo.point.lat
		newStop.route = route
		newStop.save()