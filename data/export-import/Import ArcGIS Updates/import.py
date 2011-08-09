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

changes = []
rejected = []
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
		return "None"
	
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
					changes.append('Name Change [id %s]: %s > %s' % (b.id, cb.name, b.name))
				else:
					rejected.append("Name Change Rejected")
					rejected.append(cb.json())
					rejected.append(ab)
					
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
					changes.append('Abbr Change [id %s]: %s > %s' % (b.id, cb.abbreviation, b.abbreviation))
				else:
					rejected.append("Abbreviation Change Rejected")
					rejected.append(cb.json())
					rejected.append(ab)
			
			#update coords
			ab_coords = ab['geometry']['coordinates'] if bool(ab['geometry']) else None
			ab_coords = unicode(json.dumps(ab_coords, ensure_ascii=False ))
			if not ab_coords == cb.poly_coords:
				print "%s [id: %s, abbr: %s]\n%s" % (cb.name, cb.number, cb.abbreviation, '-'*50)
				print "Coordinates changeded from/to:"
				print type(map_url(cb.poly_coords))
				print ' - Old Coords:', map_url(cb.poly_coords)
				print ' - New Coords:', map_url(ab_coords)
				if(prompt()):
					# update coords
					b = Building.objects.get( pk=ab['properties']['Num'] )
					b.poly_coords  = ab['geometry']['coordinates']
					try:
						b.clean()
						b.save()
						changes.append('Coord Changes for [id %s]: %s' % (b.id, b.name))
					except ValidationError as e:
						errors.append(
							"Unable to save building.\nError: %s\nBuilding: %s\nGeometry: %s\n\n" % (e.messages[0], ab['properties'], ab['geometry']['coordinates'])
						)
				else:
					rejected.append("New Coordinates Rejected")
					rejected.append(cb.json())
					rejected.append(ab)
			
			# item exists in old data, remove from both
			arcgis.remove(ab)
			cmap.remove(cb)

print "\n{0}\n  New Buildings \n{0}".format("-"*78)

for b in arcgis[:]:
	
	print "New Building: %s, %s" % (b['properties']['Num'], b['properties']['Name'])
	if(not prompt()):
		continue
	
	try:
		building_nums.append( b['properties']['Num'] )
		building = Building.objects.get( pk=b['properties']['Num'] )
	except Building.DoesNotExist:
		pass
	else:
		print "ERROR: How did I get here? This building should not exist: %s" % b
		exit()
	
	new = {}
	new['number']        = b['properties']['Num']
	new['name']          = b['properties']['Name']
	new['abbreviation']  = b['properties']['Abrev']
	new['poly_coords']   = b['geometry']['coordinates']
	new = Building.objects.create(**new)
	try:
		building.clean()
		building.save()
	except ValidationError as e:
		print "Unable to save building: {0} Skipped:\n  Items: {1}\n  Geometry: {1}\n\n".format(e.messages[0], b['properties'], b['geometry']['coordinates'])
		continue
	else:
		arcgis.remove(b)
		changes.append("Created new building {0}, {1}\n\n".format(new.name, new.number))


f = open('import-results.txt', 'w')
f.write("{0}\n  Changes Made \n{0}".format("-"*78))
for i in range(len(changes)):
	f.write(changes[i])

f.write("\n{0}\n  New Buildings Rejected \n{0}".format("-"*78))
for b in arcgis[:]:
	f.write(b['properties'])

f.write("\n\n{0}\n  Buildings orphaned/missing/deleted \n{0}".format("-"*78))
for b in cmap:
	f.write(b.json())

f.write("{0}\n  Rejected Changes \n{0}".format("-"*78))
for i in range(0, len(rejected), 3):
	f.write("%s\n  %s\n  %s" % (rejected[i], rejected[i+1], rejected[i+2]))
f.close()

print "Results printed to 'import-results.txt'"
print
print "Summary:"
print " %s changes" % len(changes)
print " %s rejections" % (len(rejected)/3 + len(arcgis))
print " %s orphans" % len(cmap)

