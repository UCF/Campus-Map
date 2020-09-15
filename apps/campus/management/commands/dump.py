import json
import os
import io
import sys

from django.core import serializers
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models import Q

from campus.models import MapObj
import settings
'''
    This file is used only for testing code
'''


class Command(BaseCommand):
    def handle(self, *args, **options):

        model_file = [
            ("bikerack"        , "bikeracks.json"),
            ("building"        , "buildings.json"),
            ("regionalcampus"  , "campuses.json"),
            ("group"           , "groups.json"),
            ("location"        , "locations.json"),
            ("emergencyphone"  , "phones.json"),
            ("emergencyaed"    , "aeds.json"),
            ("parkinglot"      , "parkinglots.json"),
            ("sidewalk"        , "sidewalks.json"),
            ("disabledparking" , "disabledparking.json"),
            ("electricchargingstation" , "electricchargingstations.json"),
        ]


        path = os.path.join(settings.BASE_DIR, 'apps/campus/fixtures')
        for model,file in model_file:

            print(("dumping %s ..." % model))
            f = open(os.path.join(path, file), 'w')
            output = io.StringIO()
            sys.stdout = output
            call_command('dumpdata', 'campus.%s' % model, indent=4, use_natural_keys=True)
            sys.stdout = sys.__stdout__
            txt = output.getvalue()
            f.write(txt)
            f.close

        # mapobjects has to be done uniquely
        print("dumping mapobjects ...")
        mobs = MapObj.objects.mob_filter(Q())
        f = open(os.path.join(path, '__mapobjects.json'), 'w')
        txt = serializers.serialize('json', mobs, indent=4, use_natural_keys=True)
        f.write(txt)
        f.close()

