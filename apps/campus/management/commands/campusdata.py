import os.path, re, json, campus
from django.core.management.base import BaseCommand
from django.core.management import call_command
from campus.admin import create_groupable_locations
from campus.models import Group

class Command(BaseCommand):
	args = 'none'
	help = 'load all campus fixtures'

	def handle(self, *args, **options):
		
		print "Crunching datas:"
		
		#syncdb,
		call_command('syncdb', verbosity=0, interactive=False)
		
		# reset campus
		call_command('reset', 'campus', verbosity=0, interactive=False)

		# load all the data from fixtures
		path = os.path.join(os.path.dirname(campus.__file__), 'fixtures')
		for f in os.listdir(path):
			m = re.match(r"(?P<fixture>\w+)\.json", f)
			if m:
				fixture = m.group('fixture')
				if fixture == "groups":
					continue # skip groups, must run last
				print "  Updating %s ..." % fixture
				call_command('loaddata', fixture, verbosity=0, interactive=False)
		
		# Groups
		#   for the m2m relation, create all GroupedLocation instances
		#   had to wait until all locations and contenttypes initiated
		print "  Updating groups...",
		with open(os.path.join(path, 'groups.json'), 'r') as f: txt = f.read()
		groups = json.loads(txt)
		for g in groups[:]:
			g['fields'].pop('locations')
			new = Group.objects.create(**g['fields'])
			print ".",
		print
		
		print "  Updating content types..."
		create_groupable_locations()
		
		print "  Updating m2m locations...",
		for g in groups[:]:
			locations = g['fields'].pop('locations')
			for l in locations:
				print "adding %s" % l, 
				gl = GroupedLocation.objects.get_by_natural_key(l[0], l[1])
				print gl
				new.locations.add(gl)
				print ".",
		print
		
		print "All done. The map nom'd all the data and is happy."
