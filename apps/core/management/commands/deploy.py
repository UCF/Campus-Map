from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from django.db.migrations.recorder import MigrationRecorder
from django.db import connection

from campus.models import MapObj


class Command(BaseCommand):
    help = 'Runs deployment related tasks.'

    def handle(self, *args, **options):
        # Get all the table names
        all_tables = connection.introspection.table_names()

        # Check to see if the django_migrations table exists
        if 'django_migrations' not in all_tables:
            # The showmigrations command will create the migration table if it doesn't exist
            call_command('showmigrations')
            self.stdout.write("Created migration table")

        # Get a count of migrations
        migration_count = MigrationRecorder.Migration.objects.filter(applied__isnull=False).count()

        # If there are no migrations, but the mapobj table exists, this is an existing installation
        if migration_count == 0 and 'campus_mapobj' in all_tables:
            self.stdout.write("Running initial migrations")
            call_command('migrate', '--fake-initial')
        else:
            # Run the normal migration in all other instances
            self.stdout.write("Running migrations")
            call_command('migrate')

        # Collect static files
        call_command('collectstatic', '--link', '--no-input')

        # Load in some initial testing data if no mapobj's exist yet
        if MapObj.objects.count() == 0:
            self.stdout.write("Loading in campus data")
            call_command('campusdata')


        self.stdout.write(self.style.SUCCESS("Finished deploying"))

