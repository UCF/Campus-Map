from datetime import date
import json
import logging
import urllib2
import xml.etree.ElementTree as ET

from suds.client import Client
from suds.plugin import MessagePlugin

from campus.models import ShuttleRoute
from campus.models import ShuttleStop

logger = logging.getLogger(__name__)


class Point(object):
    lat = None
    lon = None

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def json(self):
        json_object = {'lat': self.lat, 'lon': self.lon}
        return json_object


class Line(object):
    from_point = None
    to_point = None

    def __init__(self, from_point, to_point):
        self.from_point = from_point
        self.to_point = to_point


class RouteInfo(object):
    id = None
    shortname = None
    color = None
    cateogry = None
    description = None

    def __init__(self, id, shortname, color, category, description):
        self.id = id
        self.shortname = shortname
        self.color = color
        self.category = category
        self.description = description

    def json(self):
        json_object = {
            'id': self.id,
            'shortname': self.shortname,
            'color': self.color,
            'category': self.category,
            'description': self.description,
        }
        return json_object


class RouteStop(object):
    id = None
    name = None
    point = None

    def __init__(self, id, name, point):
        self.id = id
        self.name = name
        self.point = point

    def json(self):
        json_object = {'id': self.id, 'name': self.name, 'lat': self.point.lat, 'lon': self.point.lon}
        return json_object


class ShuttleGps(object):
    id = None
    point = None
    next_stop = None

    def __init__(self, id, point, next_stop):
        self.id = id
        self.point = point
        self.next_stop = next_stop

    def json(self):
        json_object = {'id': self.id, 'lat': self.point.lat, 'lon': self.point.lon, 'nextStop': self.next_stop}
        return json_object


class ShuttleRouteAPI(object):
    app_code = ''
    cost_center_id = ''
    client = None
    route_list = {}

    def __init__(self, wsdl_url, app_code, cost_center_id):
        self.app_code = app_code
        self.cost_center_id = cost_center_id

        try:
            self.client = Client(url=wsdl_url, timeout=10)
        except urllib2.URLError:
            #allow application to run without the feature
            logger.error('Could not connect to shuttle API.')
        except Exception, e:
            logger.error('Generic exception connecting to shuttle API', e.value)

    def get_routes(self):
        """
        Get the list of routes.
        """
        if not self.route_list and self.client is not None:

            try:
                routes_response = self.client.service.GetRoutes(sAppCode=self.app_code,
                                                            sCostcenterId=self.cost_center_id,
                                                            nDate=date.today().strftime('%Y%m%d'))
                print routes_response
            except Exception, e:
                logger.error('Could not retrieve routes', e.message)
                return None

            if routes_response is not None:
                xml_route_list = ET.fromstring(routes_response)
                stored_shuttle_routes = ShuttleRoute.objects.all()

                route_list = {}
                for xml_route in xml_route_list:
                    route_id = xml_route.find('ShadowRouteId').text
                    shortname = xml_route.find('Shortname').text
                    color = xml_route.find('RouteColor').text
                    description = xml_route.find('Direction').text
                    category = 'Other'

                    stored_route = None
                    try:
                        stored_route = stored_shuttle_routes.get(id=route_id)
                    except ShuttleRoute.DoesNotExist:
                        pass

                    if stored_route:
                        if stored_route.shortname:
                            shortname = stored_route.shortname

                        if stored_route.description:
                            description = stored_route.description

                        if stored_route.category:
                            category = stored_route.category.name

                    shortname = shortname.title()

                    if not color:
                        color = 'ffffff00'

                    route_list[route_id] = RouteInfo(route_id, shortname, color, category, description)

                self.route_list = route_list
            else:
                logger.error('Bad response for shuttle routes.')

        return self.route_list

    def get_route_info(self, route_id):
        """
        Get the route for a given route.
        """
        route_list = self.get_routes()
        route_info = {}
        if route_id in route_list.keys():
            route_info = route_list[route_id]

        return route_info

    def get_route_stops(self, route_id):
        """
        Get the routes stops.
        """
        stops = []
        if self.client is not None:
            stops_response = self.client.service.GetStops(sAppCode=self.app_code,
                                                          sCostCenterId=self.cost_center_id,
                                                          nDate=date.today().strftime('%Y%m%d'),
                                                          nShadowRouteId=route_id)

            if stops_response is not None:
                # Can't properly parse ampersand
                stops_response = stops_response.replace('&', '&amp;');
                xml_stop_list = ET.fromstring(stops_response)
                for xml_stop in xml_stop_list:
                    stops.append(RouteStop(xml_stop.find('ShadowStopId').text,
                                                         xml_stop.find('StopName').text,
                                                         Point(lat=xml_stop.find('Lat').text,
                                                               lon=xml_stop.find('Lon').text)))
            else:
                logger.error('Bad response for shuttle stops.')
        return stops

    def get_all_shuttle_stops_dict(self):
        """
        Get all the shuttle stops
        """
        routes = ShuttleRoute.objects.all()
        stored_stops = ShuttleStop.objects.all()
        stops = {}
        if routes is not None:

            for route in routes:
                route_stops = stored_stops.filter(route_id=route.id)
                for stop in route_stops:
                    if stop.id not in stops.keys():
                        stop_dict = stop.json()
                        stop_dict['routes'] = []
                    else:
                        stop_dict = stops[stop.id]

                    stop_dict['routes'].append({'id': route.id, 'shortname': route.shortname})
                    stops[stop.id] = stop_dict

            stops = list(stops.values())
        return stops

    def get_route_poly(self, route_id):
        """
        Get the route polygon
        """
        lines = []
        if self.client is not None:
            polygon_response = self.client.service.GetRoutePolygon(sAppCode=self.app_code,
                                                                   sCostcenterId=self.cost_center_id,
                                                                   nShadowRouteId=route_id)
            if polygon_response is not None:
                xml_polygon_list = ET.fromstring(polygon_response)
                for xml_polygon in xml_polygon_list:
                    from_point = Point(lat=xml_polygon.find('FromLat').text, lon=xml_polygon.find('FromLon').text)
                    to_point = Point(lat=xml_polygon.find('ToLat').text, lon=xml_polygon.find('ToLon').text)
                    line = Line(from_point, to_point)
                    lines.append(line)
            else:
                logger.error('Bad response for shuttle poly.')
        return lines

    def get_route_gps(self, route_id, stop_id=None):
        """
        Get the route GPS data.
        """
        if stop_id is None:
            stops = self.get_route_stops(route_id)
            if stops:
                stop_id = stops[0].id

        gps_list = []
        if self.client is not None and stop_id is not None:
            prediction_response = self.client.service.GetPredictions(sAppCode=self.app_code,
                                                                     sCostcenterId=self.cost_center_id,
                                                                     nShadowRouteId=route_id,
                                                                     nShadowStopId=stop_id,
                                                                     nMaxPredictions=10)
            if prediction_response is not None:
                xml_prediction_list = ET.fromstring(prediction_response)
                vehicles = []
                for xml_prediction in xml_prediction_list:
                    if xml_prediction.find('GPSTime').text and xml_prediction.find('Vehicle').text and xml_prediction.find('Vehicle').text not in vehicles:
                        vehicles.append(xml_prediction.find('Vehicle').text);
                        gps_list.append(ShuttleGps(xml_prediction.find('Vehicle').text,
                                               Point(xml_prediction.find('Lat').text, xml_prediction.find('Lon').text),
                                               xml_prediction.find('NextStop').text))
            else:
                logger.error('Bad response for shuttle GPS.')

        return gps_list
