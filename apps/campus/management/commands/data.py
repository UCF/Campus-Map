from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands import loaddata
import os.path, re
import campus
from campus.admin import create_groupable_locations

class Command(BaseCommand):
	args = 'none'
	help = 'load all campus fixtures'

	def handle(self, *args, **options):
		
		path = os.path.join(os.path.dirname(campus.__file__), 'fixtures')
		for f in os.listdir(path):
			m = re.match(r"(?P<fixture>\w+)\.json", f)
			if m:
				fixture = m.group('fixture')
				if fixture == "groups":
					# hold on groups
					continue
				loaddata.Command().execute(fixture)
		
		# process groups, must create Grouped Locations first
		create_groupable_locations()
		loaddata.Command().execute("groups")