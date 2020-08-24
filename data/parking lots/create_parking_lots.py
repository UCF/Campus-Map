# better documentation found in ../buildings/readme.markdown

# init django project
import sys, os, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append(os.path.abspath('../../'))
from campus.models import ParkingLot
from django.core.exceptions import ValidationError

# must update sqlite db name since it is a relative path
import settings
db = settings.DATABASES['default']['NAME']
if 'sqlite3' in db:
	settings.DATABASES['default']['NAME'] = os.path.abspath('../../') + '/' + db

# update buildings from the authoritative source
f = open('parking_lots_export.json')
txt = f.read()
f.close()
objects = json.loads(txt)

count = 0
for o in objects['features']:
	if o['geometry'] is None:
		print "No Geometry. Skipped"
		continue
	new = {}
	new['poly_coords'] = o['geometry']['coordinates']
	new['number']      = o['properties']['Number']
	new['name']        = o['properties']['Name']
	new['permit_type'] = o['properties']['Permit_typ']

	new = ParkingLot.objects.create(**new)
	count += 1

print "%d parking lots created" % (count,)
