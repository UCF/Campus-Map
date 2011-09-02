'''
	This file is used only for testing code
	
'''
from django.core.management.base import BaseCommand
from django.core import serializers
import os, campus, json
from apps.campus.models import MapObj
from django.core.management import call_command
import StringIO, sys
from django.db.models import Q

class Command(BaseCommand):
	def handle(self, *args, **options):

		features = []
		for m in MapObj.objects.all():
			
			properties = m.json()
			coords = properties.pop('poly_coords', None)
			for k,v in properties.items():
				if v in (None, "", "None", "none", "null"):
					properties[k] = None
				
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
		
		
		'''
		path = os.path.join(os.path.dirname(campus.__file__), 'fixtures')
		for model,file in model_file:
			
			print "dumping %s ..." % model
			f = open(os.path.join(path, file), 'w')
			output = StringIO.StringIO()
			sys.stdout = output
			call_command('dumpdata', 'campus.%s' % model, indent=4, use_natural_keys=True)
			sys.stdout = sys.__stdout__
			txt = output.getvalue()
			f.write(txt)
			f.close
		
		# mapobjects has to be done uniquely
		print "dumping mapobjects ..."
		mobs = MapObj.objects.mob_filter(Q())
		f = open(os.path.join(path, '__mapobjects.json'), 'w')
		txt = serializers.serialize('json', mobs, indent=4, use_natural_keys=True)
		f.write(txt)
		f.close()
		'''