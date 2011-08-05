# init django project
import sys, os, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append(os.path.abspath('../../../'))
from apps.campus.models import Building
from django.core.exceptions import ValidationError

# must update sqlite db name since it is a relative path
import settings
db = settings.DATABASES['default']['NAME']
if 'sqlite3' in db:
	settings.DATABASES['default']['NAME'] = os.path.abspath('../../../') + '/' + db

filename = "buildings_shp_export.json"
print "Reading contents of", filename, "..."
print

# update buildings from the authoritative source
f = open(filename)
txt = f.read()
f.close()

arcgis = json.loads(txt)['features']
arcgis = sorted(arcgis, key=lambda i:i['properties']['Num'])
cmap   = list(Building.objects.all())

changed = []
changes_rejected = []
deleted_new = []
deleted_old = []
errors      = []

def prompt():
	while(True):
		i = raw_input("Accept? [y/n] ")
		if(i == 'y'): 
			print
			return True
		elif(i == 'n'): 
			print
			return False
		else: 
			print "what?"

def map_url(coords):
	import urllib
	if coords == None or coords == "null":
		return None
	
	def flat(l):
		# recursive function to flatten array and create a a list of coordinates separated by a space
		str = ""
		for i in l:
			if type(i[0]) == type([]):
				return flat(i)
			else:
				str += ("%.6f,%.6f\n")  % (i[0], i[1])
		return str
	
	arr  = json.loads(coords)
	data = flat(arr)
	url  = "http://www.gpsvisualizer.com/map_input?form=google&google_wpt_filter_sort=0&form:data=%s%s" % ( 
	           urllib.quote("longitude,latitude\n"), urllib.quote(data) )
	return url


for ab in arcgis[:]:
	
	# look for it campus map
	for cb in cmap:
		if ab['properties']['Num'] == cb.number:
			'''
			# update name
			if not ab['properties']['Name'] == cb.name:
				print "%s [id: %s, abbr: %s]\n%s" % (cb.name, cb.number, cb.abbreviation, '-'*50)
				print "Name change (from/to):"
				print ' ', cb.name
				print ' ', ab['properties']['Name']
				if(prompt()):
					b = Building.objects.get( pk=ab['properties']['Num'] )
					b.name = ab['properties']['Name']
					b.save()
				else:
					changes_rejected.append("Name Change")
					changes_rejected.append(cb)
					changes_rejected.append(ab)
					
			#update abbreviation
			if not ab['properties']['Abrev'] == cb.abbreviation:
				print "%s [id: %s, abbr: %s]\n%s" % (cb.name, cb.number, cb.abbreviation, '-'*50)
				print "Abreviation change from/to:"
				print ' ', ("(none)", cb.abbreviation)[bool(cb.abbreviation)]
				print ' ', ab['properties']['Abrev']
				if(prompt()):
					b = Building.objects.get( pk=ab['properties']['Num'] )
					b.abbreviation = ab['properties']['Abrev']
					b.save()
				else:
					changes_rejected.append("Abbreviation Change")
					changes_rejected.append(cb)
					changes_rejected.append(ab)
			'''
			
			#update coords
			ab_coords = ab['geometry']['coordinates'] if bool(ab['geometry']) else None
			ab_coords = unicode(json.dumps(ab_coords, ensure_ascii=False ))
			if not ab_coords == cb.poly_coords:
				print "%s [id: %s, abbr: %s]\n%s" % (cb.name, cb.number, cb.abbreviation, '-'*50)
				print "Coordinates changed.  Use the two URLs below to view difference:"
				print "  - Old Coords: ", map_url(cb.poly_coords)
				print "  - New Coords: ", map_url(ab_coords)
				print
				if(prompt()):
					# update coords
					b = Building.objects.get( pk=ab['properties']['Num'] )
					b.poly_coords  = ab['geometry']['coordinates']
					try:
						b.clean()
						b.save()
					except ValidationError as e:
						errors.append(
							"Unable to save building.\nError: %s\nBuilding: %s\nGeometry: %s\n\n" % (e.messages[0], ab['properties'], ab['geometry']['coordinates'])
						)
				else:
					changes_rejected.append("Coordinates")
					changes_rejected.append(cb)
					changes_rejected.append(ab)
			
				


exit()

'''		
		
		if ab['properties']['Num'] == cb['Number']:
			
			p
			
			
			# check to see if they're the same
			for k,v in nb['properties'].items():
				if not ob['properties'][k] == nb['properties'][k]:
					changed.append(ob['properties'])
					changed.append(nb['properties'])
					break
			
			# item exists in old data, remove from both
			new['features'].remove(nb)
			old['features'].remove(ob)
			break

print "{0}\n  Updated Buildings \n{0}".format("-"*78)
for i in range(0, len(changed), 2):
	print changed[i]
	print changed[i+1]
	print

print "\n{0}\n  New Buildings \n{0}".format("-"*78)
for nb in new['features']:
	print nb['properties']

print "\n\n{0}\n  Deleted Buildings \n{0}".format("-"*78)
for ob in old['features']:
	print ob['properties']


for b in arcgis[:]:
	
'''
	


'''
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
'''