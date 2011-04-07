# better documentation found in ../buildings/readme.markdown

# init django project
import sys, os, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append(os.path.abspath('../../'))
from apps.campus.models import EmergencyPhone
from django.core.exceptions import ValidationError

# must update sqlite db name since it is a relative path
import settings
db = settings.DATABASES['default']['NAME']
if 'sqlite3' in db:
	settings.DATABASES['default']['NAME'] = os.path.abspath('../../') + '/' + db

# update buildings from the authoritative source
f = open('emergency_phones_export.json')
txt = f.read()
f.close()
objects = json.loads(txt)

count = 0
for o in objects['features']:
	if o['geometry'] is None:
		print "No Geometry. Skipped"
		continue
	new = {}
	new['googlemap_point'] = "[%f, %f]" % (o['geometry']['coordinates'][0], o['geometry']['coordinates'][1])
	new = EmergencyPhone.objects.create(**new)
	count += 1

print "%d emergency phones created" % (count,)