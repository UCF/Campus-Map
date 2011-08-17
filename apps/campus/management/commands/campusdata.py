from django.core.management.base import AppCommand, BaseCommand, CommandError
from django.core.management.commands import loaddata
import os.path, re
import campus
from campus.admin import create_groupable_locations

from django.core.management.color import no_style
from django.core.management.sql import sql_reset
from django.db import connections, transaction, DEFAULT_DB_ALIAS

class Command(BaseCommand):
	args = 'none'
	help = 'load all campus fixtures'

	def handle(self, *args, **options):
		
		# reset campus
		using = options.get('database', DEFAULT_DB_ALIAS)
		connection = connections[using]
		self.style = no_style()
		sql_list = sql_reset(campus.models, self.style, connection)
		
		try:
			cursor = connection.cursor()
			for sql in sql_list:
				cursor.execute(sql)
		except Exception, e:
			transaction.rollback_unless_managed()
			raise CommandError("Error: couldn't reset campus.  Full error: %s" % e)
		transaction.commit_unless_managed()

		# load all the data from fixtures
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
