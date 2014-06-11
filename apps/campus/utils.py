from datetime import date
import json
import urllib2
import xml.etree.ElementTree as ET

from suds.client import Client
from suds.plugin import MessagePlugin

from campus.models import BusRoute


class GoogleKmlFactory(object):
    @staticmethod
    def create_kml(doc_name=None, doc_desciption=None):
        """
        Create the base KML document
        """
        root = ET.Element('kml', xmlns='http://earth.google.com/kml/2.1')
        document = ET.SubElement(root, 'Document')

        name = ET.SubElement(document, 'name')
        if doc_name is not None:
            name.text = doc_name
        else:
            name.text = 'UCF Bus Transportation Information'

        description = ET.SubElement(document, 'description')
        if doc_name is not None:
            description.text = doc_desciption
        else:
            description.text = 'UCF Bus Transportation Information'
        return root

    @staticmethod
    def kml_get_document_node(root):
        if not isinstance(root, ET.Element):
            raise TypeError('root is xml.etree.ElementTree.Element type')

        document = root.find('Document')
        if document is None:
            raise KeyError('Document element not found in root.')
        return document

    @staticmethod
    def add_kml_point(root, lat, lon):
        document = GoogleKmlFactory.kml_get_document_node(root)
        placemark = ET.SubElement(document, 'Placemark')
        placemark_name = ET.SubElement(placemark, 'name')
        placemark_name.text = 'Name'
        placemark_description = ET.SubElement(placemark, 'description')
        placemark_description.text = 'Description'
        point = ET.SubElement(placemark, 'Point')
        coordinates = ET.SubElement(point, 'coordinates')
        coordinates.text = lon + ',' + lat + ',0'
        return coordinates

    @staticmethod
    def add_kml_linestring(root, coordinate_linestring, line_color=None):
        document = GoogleKmlFactory.kml_get_document_node(root)
        placemark = ET.SubElement(document, 'Placemark')
        placemark_name = ET.SubElement(placemark, 'name')

        if line_color is not None:
            style_url = ET.SubElement(placemark, 'sytleUrl')
            style_url.text = '#' + line_color

        placemark_name.text = 'Intersection'
        placemark_line_string = ET.SubElement(placemark, 'LineString')
        altitude_mode = ET.SubElement(placemark_line_string, 'altitudeMode')
        altitude_mode.text = 'relative'
        coordinates = ET.SubElement(placemark_line_string, 'coordinates')
        coordinates.text = coordinate_linestring
        return placemark

    @staticmethod
    def add_kml_line_style(root, style_id, color, width=4):
        document = GoogleKmlFactory.kml_get_document_node(root)
        style = ET.SubElement(document, 'Style')
        style.set('id', style_id)
        line_style = ET.SubElement(style, 'LineStyle')
        line_style_color = ET.SubElement(line_style, 'color')
        line_style_color.text = color
        line_style_width = ET.SubElement(line_style, 'width')
        line_style_width.text = str(width)
        return style


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


class BusGps(object):
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


class BusRouteAPI(object):
    app_code = ''
    cost_center_id = ''
    client = None
    route_list = {}

    def __init__(self, wsdl_url, app_code, cost_center_id):
        self.app_code = app_code
        self.cost_center_id = cost_center_id

        class NamespacePlugin(MessagePlugin):
            def marshalled(self, context):
                foo = context.envelope.getChild('Body').getChild[0]
                foo.xmlns = "http://tempuri.org/"

        try:
            self.client = Client(url=wsdl_url, plugins=[NamespacePlugin()], timeout=30)
        except urllib2.URLError:
            pass #allow application to run without the feature

    def get_routes(self):
        """
        Get the list of routes.
        """
        if not self.route_list and self.client is not None:
            print 'Retrieving Routes'

            routes_response = self.client.service.GetRoutes(sAppCode=self.app_code, sCostcenterId=self.cost_center_id, nDate=date.today().strftime('%Y%m%d'))
            xml_route_list = ET.fromstring(routes_response)
            stored_bus_routes = BusRoute.objects.all()

            route_list = {}
            for xml_route in xml_route_list:
                route_id = xml_route.find('ShadowRouteId').text
                shortname = xml_route.find('Shortname').text
                color = xml_route.find('RouteColor').text
                description = xml_route.find('Direction').text
                category = 'Other'

                stored_route = None
                try:
                    stored_route = stored_bus_routes.get(id=route_id)
                except BusRoute.DoesNotExist:
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
            stops_response = self.client.service.GetStops(sAppCode=self.app_code, sCostCenterId=self.cost_center_id, nDate=date.today().strftime('%Y%m%d'), nShadowRouteId=route_id)
            # Can't properly parse ampersand
            stops_response = stops_response.replace('&', '&amp;');
            xml_stop_list = ET.fromstring(stops_response)
            for xml_stop in xml_stop_list:
                stops.append(RouteStop(xml_stop.find('ShadowStopId').text, xml_stop.find('StopName').text, Point(lat=xml_stop.find('Lat').text, lon=xml_stop.find('Lon').text)))
        return stops

    def get_all_bus_stops_dict(self):
        """
        Get all the bus stops
        """
        routes = self.get_routes()

        stops = {}
        for route_id, route_info in routes.iteritems():
            route_stops = self.get_route_stops(route_id)
            for stop in route_stops:
                if stop.id not in stops.keys():
                    stop_dict = stop.json()
                    stop_dict['routes'] = []
                else:
                    stop_dict = stops[stop.id]

                stop_dict['routes'].append({'id': route_info.id, 'shortname': route_info.shortname})
                stops[stop.id] = stop_dict

        stops = list(stops.values())
        return stops

    def get_route_poly(self, route_id):
        """
        Get the route polygon
        """
        lines = []
        if self.client is not None:
            polygon_response = self.client.service.GetRoutePolygon(sAppCode=self.app_code, sCostcenterId=self.cost_center_id, nShadowRouteId=route_id)
            if polygon_response is not None:
                xml_polygon_list = ET.fromstring(polygon_response)
                for xml_polygon in xml_polygon_list:
                    from_point = Point(lat=xml_polygon.find('FromLat').text, lon=xml_polygon.find('FromLon').text)
                    to_point = Point(lat=xml_polygon.find('ToLat').text, lon=xml_polygon.find('ToLon').text)
                    line = Line(from_point, to_point)
                    lines.append(line)
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
            prediction_response = self.client.service.GetPredictions(sAppCode=self.app_code, sCostcenterId=self.cost_center_id, nShadowRouteId=route_id, nShadowStopId=stop_id, nMaxPredictions=10)
            xml_prediction_list = ET.fromstring(prediction_response)
            vehicles = []
            for xml_prediction in xml_prediction_list:
                if xml_prediction.find('GPSTime').text and xml_prediction.find('Vehicle').text and xml_prediction.find('Vehicle').text not in vehicles:
                    vehicles.append(xml_prediction.find('Vehicle').text);
                    gps_list.append(BusGps(xml_prediction.find('Vehicle').text,
                                           Point(xml_prediction.find('Lat').text, xml_prediction.find('Lon').text),
                                           xml_prediction.find('NextStop').text))


        return gps_list


def get_geo_data(lat, lng):
    """
    Get geo location data for tagging
    """
    geo_placename = None
    geo_state = None
    geo_country = None
    geo_url = 'http://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s&sensor=false' % (str(lat), str(lng),)
    geo_request = json.load(urllib2.urlopen(geo_url))
    geo_results = geo_request.get('results')
    if len(geo_results):
        for geo_addr in geo_results:
            for geo_addr_comp in geo_addr.get('address_components'):
                if geo_placename is None and 'locality' in geo_addr_comp.get('types'):
                    geo_placename = geo_addr_comp.get('long_name')

                if geo_state is None and 'administrative_area_level_1' in geo_addr_comp.get('types'):
                    geo_state = geo_addr_comp.get('short_name')

                if geo_country is None and 'country' in geo_addr_comp.get('types'):
                    geo_country = geo_addr_comp.get('short_name')

                if geo_placename and geo_state and geo_country:
                    return (geo_placename, geo_country + '-' + geo_state)

    return (geo_placename, geo_country + '-' + geo_state if geo_country and geo_state else None)
