import os.path, re, campus
from django.core.management.base import BaseCommand
from django.core.management import call_command
from campus.admin import create_groupable_locations

class Command(BaseCommand):
	args = 'none'
	help = 'load all campus fixtures'

	def handle(self, *args, **options):
		
		print "Crunching datas:"
		
		#syncdb,
		call_command('syncdb', verbosity=0)
		
		# reset campus
		call_command('reset', 'campus', interactive=False)

		# load all the data from fixtures
		path = os.path.join(os.path.dirname(campus.__file__), 'fixtures')
		for f in os.listdir(path):
			m = re.match(r"(?P<fixture>\w+)\.json", f)
			if m:
				fixture = m.group('fixture')
				if fixture == "groups":
					continue # skip groups, must run last
				print "  Updating %s ..." % fixture
				call_command('loaddata', fixture, verbosity=0)
		
		# Groups
		#   for the m2m relation, create all GroupedLocation instances
		#   had to wait until all locations and contenttypes initiated
		print "  Updating content types..."
		create_groupable_locations()
		print "  Updating groups ..."
		call_command('loaddata', 'groups', verbosity=0)
		
		print "All done. The map nom'd all the data and is happy."
