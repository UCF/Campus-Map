import StringIO
import sys
import json
import os

from django.core import serializers
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.campus.models import MapObj
import campus
'''
    This was needed at some point (testing 3rd party system for displaying geodata)
    Not so much needed now, only kept for posterity.

'''


class Command(BaseCommand):
    def handle(self, *args, **options):

        features = []
        for m in MapObj.objects.all():

            properties = m.json(base_url='http://map.ucf.edu')
            properties.pop('link', None)
            coords = properties.pop('poly_coords', None)
            if not coords:
                coords = []

            # because keys can only be 10char long
            shortened_key = {
                'description'       : 'excerpt',
                'object_type'       : 'obj_type',
                'permit_type'       : 'perm_type',
                'abbreviation'      : 'abbrev',
                'illustrated_point' : 'ill_point',
                'googlemap_point'   : 'gmap_point',
                'profile_link'      : 'prof_link',
            }

            for k,v in properties.items():
                properties[k] = str(v)
                if v in ("", "None", "none", "null"):
                    v = None
                if shortened_key.get(k, False):
                    del(properties[k])
                    k = shortened_key[k]
                if v:
                    v = str(v)
                properties[k] = v

            feature = {
                "type": "Feature",
                "properties": properties,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coords,
                }
            }

            features.append(feature)

        geo = {
            "type": "FeatureCollection",
            "features": features,
        }
        geo = json.dumps(geo, indent=4)

        # place on desktop
        path = os.path.expanduser('~/Desktop/campus_map.geo.json')
        f = open(path, 'w')
        f.write(geo)
        f.close()
        print "Exported to %s" % path

