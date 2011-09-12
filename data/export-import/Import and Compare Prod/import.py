# init django project
import sys, os, json, re
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append(os.path.abspath('../../../'))
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from campus.models import MapObj, Group
from tools import *

# must update sqlite db name since it is a relative path
import settings
db = settings.DATABASES['default']['NAME']
if 'sqlite3' in db:
	settings.DATABASES['default']['NAME'] = os.path.abspath('../../../') + '/' + db


print "Looking at desktop for map export ..."
path = os.path.expanduser('~/Desktop/')
files = os.listdir(path)
files.sort()

export = None
for f in files:
	m = re.match(r"(?P<export>.+)\.json$", f)
	if m:
		print 'Continue with "%s"?' % f
		if prompt():
			export = f
			break
if not export:
	print "Export not found.  Goodbye."
	exit()

# output
printo(None, file="import-results.txt")

printo("Reading contents of \"%s\" \n" % export)
export = os.path.join(path, export)

# update buildings from the authoritative source
f = open(export)
txt = f.read()
f.close()

prod   = json.loads(txt)
cmap   = list(MapObj.objects.all())

printo("\n{0}\n  Inspecting Updates \n{0}\n".format("-"*78))

def _(str):
	if str=='':    return "(empty string)"
	if str==None:  return "(none)"
	if str==False: return "(false)"
	return str

results = {
	'Accepted' : 0,
	'Rejected' : 0,
}

def compare(mob, o):
	mob = mob.__dict__
	mob.pop('_state', None)
	for k,v in o['fields'].items():
		try:
			if not mob[k]==v:
				
				# None vs ""
				if mob[k] == None and v == "":
					printo("Empty string: %s [%s]" % (mob['name'], mob['id']))
					if(results.get('Empty Strings', False)):
						results['Empty Strings'] += 1
					else:
						results['Empty Strings'] = 1
					continue
				
				printo("%s [%s]" % (mob['name'], mob['id']))
				printo("  %s %s" % (k, _(mob[k])))
				printo("  %s %s" % (k, _(v)))
				if prompt():
					m = MapObj.objects.get(id=o['pk'])
					setattr(m,k,v)
					m.save()
					printo('accepted')
					results['Accepted'] += 1
				else:
					printo('rejected')
					results['Rejected'] += 1
				printo('')
				
		except KeyError:
			
			# if locations
			if k == 'locations':
				g = Group.objects.get(id=o['pk'])
				g_locs = []
				for l in g.locations.all():
					g_locs.append(l.content_object.id)
				for l in o['fields']['locations']:
					try:
						g_locs.remove(l[1])
					except ValueError:
						printo("Location Missing in Group: [%s] in [%s]" % (l[1], o['pk']))
						if(results.get('M2M missing', False)): results['M2M missing'] += 1
						else: results['M2M missing'] = 1
				if len(g_locs) > 0:
					for l in g_locs:
						printo("Location Removed in Group: [%s] in [%s]" % (l, o['pk']))
						if(results.get('M2M removed', False)): results['M2M removed'] += 1
						else: results['M2M removed'] = 1
				continue
			
			if(results.get('Key Errors', False)): results['Key Errors'] += 1
			else: results['Key Errors'] = 1
			
			
			str1 = "Key Error: %s %s" % (mob['id'], o['model'])
			
			val = o['fields'].get(k, "(key error)")
			val = str(val)
			val = (val[:75] + ' ..') if len(val) > 75 else val
			str2 = "  |  o['%s']: %-15s" % (k,val)
			
			val = mob.get(k, "(key error)")
			val = str(val)
			val = (val[:75] + ' ..') if len(val) > 75 else val
			str3 = "  |  mob['%s']: %-15s" % (k, val)
			
			printo(str1 + str2 + str3)

for o in prod:
	
	app_label, model = o['model'].split(".")
	ct = ContentType.objects.get(app_label=app_label, model=model)
	try:
		mob = ct.get_object_for_this_type(pk=o['pk'])
		compare(mob, o)
		
	except ObjectDoesNotExist:
		try:
			if str(model) == "emergencyphone":
				id = '-'.join(['phone',str(o['pk'])])
			elif str(model) == "group":
				id = o['fields']['slug']
			else:
				id = '-'.join([str(model),str(o['pk'])])
			mob = ct.get_object_for_this_type(pk=id)
			compare(mob, o)
			
		except ObjectDoesNotExist:
			printo("Missing Locally: %s %s %s" % (ct, o['pk'], o.get('name', '')))
			if(results.get('Missing locally', False)): results['Missing locally'] += 1
			else: results['Missing locally'] = 1

printo("\n\nResults:")
for k,v in results.items():
	printo("  %s: %-5s" % (k,v))

print
print "Output in import-results.txt"
