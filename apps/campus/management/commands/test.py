from django.core.management.base import BaseCommand
import os, campus, json
from apps.campus.models import Building, RegionalCampus, Location, Group
from campus.admin import create_groupable_locations

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
		
		create_groupable_locations()
		
		# Groups
		f = open(os.path.join(path, 'groups.json'), 'r')
		txt = f.read()
		f.close()
		objects = json.loads(txt)
		for o in objects:
			o['fields']['id'] = o['pk']
			new = Group.objects.create(**o['fields'])
			print new.id
		