import json
import logging
import xml.etree.ElementTree as ET

from django.conf import settings
import requests


logger = logging.getLogger(__name__)


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
            name.text = 'UCF Shuttle Transportation Information'

        description = ET.SubElement(document, 'description')
        if doc_name is not None:
            description.text = doc_desciption
        else:
            description.text = 'UCF Suttle Transportation Information'
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


def get_geo_data(lat, lng):
    """
    Get geo location data for tagging
    """
    geo_placename = None
    geo_state = None
    geo_country = None
    geo_url = 'http://maps.googleapis.com/maps/api/geocode/json'
    try:
        geo_request = requests.get(geo_url,
                                   params={'latlng': str(lat) + ',' + str(lng), 'sensor': 'false'},
                                   timeout=settings.REQUEST_TIMEOUT).json()
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
    except Exception as e:
        logger.error('Error getting geo data: ' + str(e))

    return (geo_placename, geo_country + '-' + geo_state if geo_country and geo_state else None)
