from datetime import datetime

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
	if coords == None or coords == "null" or coords == "None":
		return "None"
	
	def flat(l):
		# recursive function to flatten array and create a a list of coordinates separated by a space
		str = ""
		for i in l:
			if type(i[0]) == type([]):
				str += flat(i)
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

out = None
def printo(str, file=False):
	global out
	
	if(file):
		out = open("import-results.txt", "a")
		out.write("\n\n%s %s\n\n" % ('>'*20, datetime.now().strftime("%A %B %d, %Y %H:%M")))
		return
	
	print str
	out.write(str)
	out.write("\n")