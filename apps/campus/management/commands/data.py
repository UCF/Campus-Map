from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands import loaddata
import os.path, re
import campus

class Command(BaseCommand):
	args = 'none'
	help = 'load all campus fixtures'

	def handle(self, *args, **options):
		
		path = os.path.join(os.path.dirname(campus.__file__), 'fixtures')
		for f in os.listdir(path):
			m = re.match(r"(?P<fixture>\w+)\.json", f)
			if m:
				fixture = m.group('fixture')
				loaddata.Command().execute(fixture)