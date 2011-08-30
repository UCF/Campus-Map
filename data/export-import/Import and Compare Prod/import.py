# init django project
import sys, os, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.append(os.path.abspath('../../../'))
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from campus.models import MapObj
from tools import *

# must update sqlite db name since it is a relative path
import settings
db = settings.DATABASES['default']['NAME']
if 'sqlite3' in db:
	settings.DATABASES['default']['NAME'] = os.path.abspath('../../../') + '/' + db

filename = "UCF Campus Map 2011-08-30.json"
print "Reading contents of", filename, "..."
print

# update buildings from the authoritative source
f = open(filename)
txt = f.read()
f.close()

prod   = json.loads(txt)
cmap   = list(MapObj.objects.all())

# output
printo(None, file="import-results.txt")


printo("\n{0}\n  Inspecting Updates \n{0}\n".format("-"*78))

def _(str):
	if str=='':    return "(empty string)"
	if str==None:  return "(none)"
	if str==False: return "(false)"
	return str

def compare(mob, o):
	mob = mob.__dict__
	mob.pop('_state', None)
	for k,v in o['fields'].items():
		try:
			if not mob[k]==v:
				print "Changes", mob['id']
				print "  ", k, _(mob[k])
				print "  ", k, _(v)
				print
		except KeyError:
			print o['fields'].get('name'), o['model']
			
			
			val = o['fields'].get(k, "(key error)")
			val = str(val)
			val = (val[:75] + ' ..') if len(val) > 75 else val
			print "    o['%s']: %-15s" % (k,val)
			
			val = mob.get(k, "(key error)")
			val = str(val)
			val = (val[:75] + ' ..') if len(val) > 75 else val
			print "  mob['%s']: %-15s" % (k, val)
			print
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
			print "Can't Find:", ct, o['pk'], o.get('name', '')
			print