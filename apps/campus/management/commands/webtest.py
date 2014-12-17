import time

from django.core.management.base import BaseCommand
import requests
from requests.exceptions import MissingSchema


'''
    Check a series of URLs and make sure we get a response

'''
class Command(BaseCommand):
    def handle(self, *args, **options):

        if len(args):
            try:
                requests.get(args[0])
                base = args[0]
            except MissingSchema:
                base = "http://%s/" % args[0]
        else:
            print "No host given, using 'my.mac'"
            base = "http://my.mac/"

        from settings import MAP_VERSION

        url_strings = [
            '',
            '.json',
            'search/.json?q=commons',
            'search/',
            'organizations/',
            'organizations/354/',
            'organizations/354/.json',
            'organizations/96/.ajax',
            'locations/',
            "locations.kml",
            'locations.json',
            "locations.kml?v=%s" % MAP_VERSION,
            'locations/.json',
            "locations/52/.json",
            "locations/52.json",
            "locations/52/student-union/",
            "locations/52/student-union.json",
            'locations/1/millican-hall/?org=354',
            'printable/',
            "parking.kml?v=%s" % MAP_VERSION,
            "sidewalks.kml?v=%s" % MAP_VERSION,
            "bikeracks.json",
            "emergency-phones.json",
        ]

        for u in url_strings:
            try:
                url = base+u
                print "%-75s " % url,
                page = requests.get(url, timeout=10)
                print "OK"
                page.close()

            except Exception, e:
                print "Fail: %s" % str(e)
