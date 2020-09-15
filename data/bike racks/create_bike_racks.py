# better documentation found in ../buildings/readme.markdown

# init django project
import sys, os, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append(os.path.abspath('../../'))
from campus.models import BikeRack
from django.core.exceptions import ValidationError

# must update sqlite db name since it is a relative path
import settings
db = settings.DATABASES['default']['NAME']
if 'sqlite3' in db:
	settings.DATABASES['default']['NAME'] = os.path.abspath('../../') + '/' + db

# update buildings from the authoritative source
f = open('bike_racks_export.json')
txt = f.read()
f.close()
racks = json.loads(txt)

count = 0
for r in racks['features']:
	if r['geometry'] is None:
		print("No Geometry. Skipped")
		continue
	new = {}
	new['id']              = r['properties']['ID']
	new['googlemap_point'] = "[%f, %f]" % (r['geometry']['coordinates'][1], r['geometry']['coordinates'][0])
	# ignoring buildings because we only have name and not building id
	new = BikeRack.objects.create(**new)
	count += 1

print(("%d bike racks plotted" % (count,)))
