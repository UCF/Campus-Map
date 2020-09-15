# better documentation found in ../buildings/readme.markdown

# init django project
import sys, os, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append(os.path.abspath('../../'))
from campus.models import Sidewalk
from django.core.exceptions import ValidationError

# must update sqlite db name since it is a relative path
import settings
db = settings.DATABASES['default']['NAME']
if 'sqlite3' in db:
	settings.DATABASES['default']['NAME'] = os.path.abspath('../../') + '/' + db

# update buildings from the authoritative source
f = open('sidewalks_export.json')
txt = f.read()
f.close()
sidewalks = json.loads(txt)

count = 0
for s in sidewalks['features']:
	if s['geometry'] is None:
		print("No Geometry. Skipped")
		continue
	new = {}
	new['poly_coords']   = s['geometry']['coordinates']
	new = Sidewalk.objects.create(**new)
	count += 1

print(("%d sidewalks created" % (count,)))
