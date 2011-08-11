# init django project
import sys, os, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append(os.path.abspath('../../../'))
from apps.campus.models import Building
from django.core.exceptions import ValidationError
from datetime import datetime

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

# output
out = open("import-results.txt", "a")
out.write("%s %s\n\n" % ('>'*20, datetime.now().strftime("%A %B %d, %Y %H:%M")))

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

def coords(obj):
	if isinstance(obj, Building):
		return str(obj.poly_coords)
	else:
		try: obj_coords = obj['geometry']['coordinates']
		except: obj_coords = None
		return unicode(json.dumps(obj_coords, ensure_ascii=False ))

def abbr(obj):
	if isinstance(obj, Building):
		return "(none)" if not bool(obj.abbreviation) else obj.abbreviation
	else:
		return "(none)" if not bool(obj['properties']['Abrev']) else obj['properties']['Abrev']

def printo(str):
	print str
	out.write(str)
	out.write("\n")


# find / remove duplicates
for a in arcgis[:]:
	duplicates = []
	for b in arcgis[:]:
		if a['properties']['Num'] == b['properties']['Num']:
			duplicates.append(b)
	if len(duplicates) > 1:
		printo("\n{0}\n  Found Duplicates \n{0}".format("-"*78))
		for i,d in enumerate(duplicates):
			printo("#%s\n  %s [%s]\n  %s\n" % (i+1, d['properties']['Name'], d['properties']['Num'], coords(d)))
		
		select = raw_input("Select which to keep (1-%s, 0 for none): " % len(duplicates))
		try: select = int(select)
		except ValueError: select = 0
		print
		
		for i,d in enumerate(duplicates):
			if (i+1) == select:
				continue
			arcgis.remove(d)


printo("\n{0}\n  Inspecting Updates \n{0}\n".format("-"*78))

for ab in arcgis[:]:
	
	# look for it campus map
	for cb in cmap[:]:
		if ab['properties']['Num'] == cb.number:
			
			# update name
			if not ab['properties']['Name'] == cb.name:
				print "%s [id: %s]\n%s" % (cb.name, cb.number, '-'*50)
				print "Name change (from/to):"
				print ' ', cb.name
				print ' ', ab['properties']['Name']
				if(prompt()):
					b = Building.objects.get( pk=ab['properties']['Num'] )
					b.name = ab['properties']['Name']
					b.save()
					out.write("--- Updated Name, ID:%s ---\n" % b.number)
					out.write('  %s\n  %s\n\n' % (cb.name, b.name))
				else:
					out.write("XXXXX Rejected Name Change, ID:%s XXXXX\n" % cb.number)
					out.write('  %s\n  %s\n\n' % (cb.name, ab['properties']['Name']))
					
			#update abbreviation
			if not ab['properties']['Abrev'] == cb.abbreviation:
				print "%s [id: %s]\n%s" % (cb.name, cb.number, '-'*50)
				print "Abreviation change from/to:"
				print ' ', abbr(cb)
				print ' ', abbr(ab)
				if(prompt()):
					b = Building.objects.get( pk=ab['properties']['Num'] )
					b.abbreviation = ab['properties']['Abrev']
					b.save()
					out.write("--- Updated Abbreviation, %s ---\n" % b.name)
					out.write('  %s\n  %s\n\n' % (abbr(cb), abbr(b)))
				else:
					out.write("XXXXX Rejected Abbreviation Change, %s XXXXX\n" % cb.name)
					out.write('  %s\n  %s\n\n' % (abbr(cb), abbr(ab)))
			
			#update coords
			try: ab_coords = ab['geometry']['coordinates']
			except: ab_coords = None
			ab_coords = unicode(json.dumps(ab_coords, ensure_ascii=False ))
			if not ab_coords == cb.poly_coords:
				print "%s [id: %s]\n%s" % (cb.name, cb.number, '-'*50)
				print "Coordinates changeded from/to:"
				print ' - Old Coords:', map_url(cb.poly_coords)
				print ' - New Coords:', map_url(ab_coords)
				if(prompt()):
					# update coords
					b = Building.objects.get( pk=ab['properties']['Num'] )
					try:
						b.poly_coords  = ab['geometry']['coordinates']
						b.clean()
						b.save()
						out.write("--- Updated Coordinates, %s ---\n" % b.name)
						out.write("  %s\n  %s\n\n" % (cb.poly_coords, b.poly_coords))
					except (TypeError, ValidationError) as e:
						e_str = str(e) if not hasattr(e, 'messages') else e.messages[0]
						out_str = "\n{0}\n  Error - Unable to save building \n{0}\n  Error: {1}\n  Building: {2}\n  Geometry: {3}\n\n".format(
							"X"*78, e_str, ab['properties'], ab_coords)
						out.write(out_str)
						print
						print out_str
				else:
					out.write("XXXXX Rejected Coordinates, %s XXXXX\n" % cb.name)
					out.write("  %s\n  %s\n\n" % (coords(cb), coords(ab)))
			
			# item exists in old data, remove from both
			arcgis.remove(ab)
			cmap.remove(cb)
			out.flush()


print "\n{0}\n  New Buildings \n{0}\n".format("-"*78)
if not len(arcgis):
	print("  None.\n")
for b in arcgis[:]:
	
	print "New Building: %s, %s" % (b['properties']['Num'], b['properties']['Name'])
	print "  coords: %s" % map_url(coords(b))
	if(not prompt()):
		continue
	
	try:
		building = Building.objects.get( pk=b['properties']['Num'] )
	except Building.DoesNotExist:
		pass
	else:
		print "\n\nERROR: How did I get here? This building should not exist: %s\n\nExiting.\n\n" % b
		exit()
	
	new = {}
	new['number']        = b['properties']['Num']
	new['name']          = b['properties']['Name']
	new['abbreviation']  = b['properties']['Abrev']
	new['poly_coords']   = b['geometry']['coordinates']
	nb = Building.objects.create(**new)
	try:
		nb.clean()
		nb.save()
	except ValidationError as e:
		print "Unable to save building: {0} Skipped:\n  Items: {1}\n  Geometry: {1}\n\n".format(e.messages[0], b['properties'], b['geometry']['coordinates'])
		continue
	else:
		out.write("Created New Building:\n")
		out.write("  %s\n\n" % str(nb.json()))
		arcgis.remove(b)
	
	out.flush()


printo("\n\n{0}\n  Buildings Orphaned \n{0}\n".format("-"*78))
if not len(cmap):
	printo("  None.\n")
for b in cmap:
	print "%s" % b.name
	print"  number: %s\n  abbreviation: %s\n  coords: %s" % (b.number, abbr(b), coords(b))
	print "Keep building? ",
	if(prompt()):
		out.write("%s\n" % b.name)
		out.write("  number: %s\n  abbreviation: %s\n  coords: %s\n\n" % (b.number, abbr(b), coords(b)))
	else:
		Building.objects.get( pk=b.number ).delete()
		out.write("Deleted Building:\n")
		out.write("  %s [id: %s]" % (b.name, b.number))
		cmap.remove(b)
	out.flush()


out.write("\n{0}\n  New Buildings Rejected \n{0}\n\n".format("-"*78))
if not len(arcgis):
	out.write("  None.\n\n")
for b in arcgis:
	out.write("%s\n\n" % b['properties'])


print "Results printed 'import-results.txt'"
out.close()
