import json
import os

from django.core.management.base import BaseCommand

from apps.campus.models import BikeRack
from apps.campus.models import Building
from apps.campus.models import EmergencyPhone
from apps.campus.models import EmergencyAED
from apps.campus.models import Group
from apps.campus.models import GroupedLocation
from apps.campus.models import Location
from apps.campus.models import ParkingLot
from apps.campus.models import RegionalCampus
from campus.admin import create_groupable_locations
import campus


class Command(BaseCommand):
    def handle(self, *args, **options):

        # load all the data from fixtures
        path = os.path.join(os.path.dirname(campus.__file__), 'fixtures')

        # buildings
        f = open(os.path.join(path, 'buildings.json'), 'r')
        txt = f.read()
        f.close()
        buildings = json.loads(txt)
        for b in buildings:
            b['fields']['id'] = b['pk']
            new = Building.objects.create(**b['fields'])
            print new.id, new.name

        # regional campuses
        f = open(os.path.join(path, 'campuses.json'), 'r')
        txt = f.read()
        f.close()
        objects = json.loads(txt)
        for o in objects:
            o['fields']['id'] = o['pk']
            new = RegionalCampus.objects.create(**o['fields'])
            print new.id, new.name


        # locations
        f = open(os.path.join(path, 'locations.json'), 'r')
        txt = f.read()
        f.close()
        objects = json.loads(txt)
        for o in objects:
            o['fields']['id'] = o['pk']
            new = Location.objects.create(**o['fields'])
            print new.id, new.name

        # parking lots
        f = open(os.path.join(path, 'parkinglots.json'), 'r')
        txt = f.read()
        f.close()
        objects = json.loads(txt)
        for o in objects:
            o['fields']['id'] = "parkinglot-%s" % o['pk']
            new = ParkingLot.objects.create(**o['fields'])
            print new.id, new.name

        # emergency phones
        f = open(os.path.join(path, 'phones.json'), 'r')
        txt = f.read()
        f.close()
        objects = json.loads(txt)
        for o in objects:
            o['fields']['id'] = "phone-%s" % o['pk']
            new = EmergencyPhone.objects.create(**o['fields'])
            print new.id, new.name

        # emergency aeds
        f = open(os.path.join(path, 'aeds.json'), 'r')
        txt = f.read()
        f.close()
        objects = json.loads(txt)
        for o in objects:
            o['fields']['id'] = "aed-%s" % o['pk']
            new = EmergencyPhone.objects.create(**o['fields'])
            print new.id, new.name

        # bike racks
        f = open(os.path.join(path, 'bikeracks.json'), 'r')
        txt = f.read()
        f.close()
        objects = json.loads(txt)
        for o in objects:
            o['fields']['id'] = "bikerack-%s" % o['pk']
            new = BikeRack.objects.create(**o['fields'])
            print new.id, new.name

        create_groupable_locations()

        # Groups
        f = open(os.path.join(path, 'groups.json'), 'r')
        txt = f.read()
        f.close()
        objects = json.loads(txt)
        for o in objects[:]:
            o['fields']['id'] = o['pk']
            locations = o['fields'].pop('locations')
            new = Group.objects.create(**o['fields'])
            print new.id
            for l in locations:
                print "adding %s" % l,
                gl = GroupedLocation.objects.get_by_natural_key(l[0], l[1])
                print gl
                new.locations.add(gl)
