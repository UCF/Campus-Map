# init django project
import sys, os, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append(os.path.abspath('../../'))
from apps.campus.models import Building
from django.core.exceptions import ValidationError

# must update sqlite db name since it is a relative path
import settings
db = settings.DATABASES['default']['NAME']
if 'sqlite3' in db:
	settings.DATABASES['default']['NAME'] = os.path.abspath('../../') + '/' + db

# reset building database from old map
if "destroy" in sys.argv:
	
	print "{0}\n  Destroying all buildings and importing from old  \n{0}".format("-"*78)
	
	buildings = Building.objects.all()
	for b in buildings:
		b.delete()
		
	# import building data from old webcom map, this includes pictures
	# and point location in both gmap and illustrated map
	f = open('old_map_dump.json', 'r')
	txt = f.read()
	f.close()
	buildings = json.loads(txt)

	for b in buildings:
		new = {}
		new['number']            = b['pk'].lower()
		new['name']              = b['fields']['name']
		new['abbreviation']      = b['fields']['abbreviation']
		new['image']             = b['fields']['image']
		new['description']       = b['fields']['description']
		
		if(		b['fields']['coord_x'] != None 
			and b['fields']['coord_x'] != ""
			and b['fields']['coord_y'] != None
			and b['fields']['coord_y'] != ""
		): new['googlemap_point']   = "[{0}, {1}]".format(b['fields']['coord_x'], b['fields']['coord_y'])
		else: new['googlemap_point'] = ""
		
		if(		b['fields']['ill_coord_x'] != None 
			and b['fields']['ill_coord_x'] != "" 
			and b['fields']['ill_coord_y'] != None
			and b['fields']['ill_coord_y'] != ""
		): new['illustrated_point'] = "[{0}, {1}]".format(b['fields']['ill_coord_x'], b['fields']['ill_coord_y'])
		else: new['illustrated_point'] = None
		new = Building(**new)
		new.clean()
		new.save()

	print
	print


# update buildings from the authoritative source
f = open('buildings_export.json')
txt = f.read()
f.close()
buildings = json.loads(txt)

building_nums = []
for b in buildings['features']:
	# ignore bad numbers, names, geometry, and duplicates
	if b['properties']['Num']==None or b['properties']['Num']=='0' or b['properties']['Num'].strip()=='':
		print "Invalid number.  Skipped:\n  Items: {0}\n  Geometry: {1}\n\n".format(b['properties'], b['geometry']['coordinates'])
		continue
	else:
		# fix building numbers to all be lowercase
		b['properties']['Num'] = b['properties']['Num'].lower()
	if b['properties']['Name']==None or b['properties']['Name'].strip()=='':
		print "Invalid name.  Skipped:\n  Items: {0}\n  Geometry: {1}\n\n".format(b['properties'], b['geometry']['coordinates'])
		continue
	if b['properties']['Num'] in building_nums:
		print "Duplicate Buildings.  Using only the first:"
		for temp in buildings['features']:
			if temp['properties']['Num'] == b['properties']['Num']:
				print "  Old Building {0}".format(temp['properties'])
		print "\n"
		continue
	if b['geometry'] is None:
		print "No Geometry. Skipped:\n  Items: {0}\n\n".format(b['properties'])
		continue
	try:
		building_nums.append( b['properties']['Num'] )
		building = Building.objects.get( pk=b['properties']['Num'] )
	except Building.DoesNotExist:
		new = {}
		new['number']        = b['properties']['Num']
		new['name']          = b['properties']['Name']
		new['abbreviation']  = b['properties']['Abrev']
		new['poly_coords']   = b['geometry']['coordinates']
		new = Building.objects.create(**new)
		print "Created new building {0}, {1}\n\n".format(new.name, new.number)
	else:
		before_update = building.json()
		building = Building.objects.get( pk=b['properties']['Num'] )
		building.name         = b['properties']['Name']
		building.abbreviation = b['properties']['Abrev']
		building.poly_coords  = b['geometry']['coordinates']
		try:
			building.clean()
			building.save()
		except ValidationError as e:
			print "Unable to save building: {0} Skipped:\n  Items: {1}\n  Geometry: {1}\n\n".format(e.messages[0], b['properties'], b['geometry']['coordinates'])
			continue

		building = Building.objects.get( pk=b['properties']['Num'] )
		if before_update != building.json():
			print "Updated {0}:".format(building)
			for f in building.json().items():
				if f[1] != before_update[f[0]]:
					print "  From: [{0}] {1}".format(f[0], before_update[f[0]])
					print "    To: [{0}] {1}".format(f[0], f[1])
			print "\n"

# Print orphaned buildings
# building in the database but not in the authoritative source
orphans_detected = False
buildings = Building.objects.all()
for b in buildings:
	if not b.number in building_nums:
		if not orphans_detected:
			print "{0}\n  Detected buildings not present in the authoritative source \n{0}".format("-"*78)
			orphans_detected = True
		print "{0} #{1}".format(b.name, b.number)
