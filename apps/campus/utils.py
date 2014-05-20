from datetime import date
import xml.etree.ElementTree as ET

from suds.client import Client
from suds.plugin import MessagePlugin


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

    def __init__(self, id, shortname, color):
        self.id = id
        self.shortname = shortname
        self.color = color

    def json(self):
        json_object = {
            'id': self.id,
            'shortname': self.shortname,
            'color': self.color,
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
    route_list = None

    def __init__(self, wsdl_url, app_code, cost_center_id):
        self.app_code = app_code
        self.cost_center_id = cost_center_id

        class NamespacePlugin(MessagePlugin):
            def marshalled(self, context):
                foo = context.envelope.getChild('Body').getChild[0]
                foo.xmlns = "http://tempuri.org/"

        self.client = Client(url=wsdl_url, plugins=[NamespacePlugin()])

    def get_routes(self):
        """
        Get the list of routes.
        """
        if self.route_list is None:
            print 'Retrieving Routes'

            routes_response = self.client.service.GetRoutes(sAppCode=self.app_code, sCostcenterId=self.cost_center_id, nDate=date.today().strftime('%Y%m%d'))
            xml_route_list = ET.fromstring(routes_response)

            route_list = {}
            for xml_route in xml_route_list:
                route_id = xml_route.find('ShadowRouteId').text
                shortname = xml_route.find('Shortname').text
                color = xml_route.find('RouteColor').text

                if not color:
                    color = 'ffffff00'

                route_list[route_id] = RouteInfo(route_id, shortname, color)

            self.route_list = route_list
        return self.route_list

    def get_route_info(self, route_id):
        """
        Get the route for a given route.
        """
        route_list = self.get_routes()
        route_info = None
        if route_id in route_list.keys():
            route_info = route_list[route_id]

        return route_info

    def get_route_stops(self, route_id):
        """
        Get the routes stops.
        """
        stops_response = self.client.service.GetStops(sAppCode=self.app_code, sCostCenterId=self.cost_center_id, nDate=date.today().strftime('%Y%m%d'), nShadowRouteId=route_id)
        # Can't properly parse ampersand
        stops_response = stops_response.replace('&', '&amp;');
        xml_stop_list = ET.fromstring(stops_response)
        stops = []
        for xml_stop in xml_stop_list:
            stops.append(RouteStop(xml_stop.find('ShadowStopId').text, xml_stop.find('StopName').text, Point(lat=xml_stop.find('Lat').text, lon=xml_stop.find('Lon').text)))
        return stops

    def get_route_poly(self, route_id):
        """
        Get the route polygon
        """
        polygon_response = self.client.service.GetRoutePolygon(sAppCode=self.app_code, sCostcenterId=self.cost_center_id, nShadowRouteId=route_id)
        lines = []
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
            else:
                raise Http404()

        prediction_response = self.client.service.GetPredictions(sAppCode=self.app_code, sCostcenterId=self.cost_center_id, nShadowRouteId=route_id, nShadowStopId=stop_id, nMaxPredictions=10)
        xml_prediction_list = ET.fromstring(prediction_response)
        gps_list = []
        for xml_prediction in xml_prediction_list:
            if xml_prediction.find('GPSTime').text and xml_prediction.find('Vehicle').text:
                gps_list.append(BusGps(xml_prediction.find('Vehicle').text,
                                       Point(xml_prediction.find('Lat').text, xml_prediction.find('Lon').text),

                                ))

        return gps_list
