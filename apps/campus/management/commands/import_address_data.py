import csv

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection, transaction
from django.db.utils import IntegrityError, DatabaseError

from apps.campus.models import Building

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        help =  'Import addresses from CSV file'

        if args:

            path = args[0]

            self.stdout.write('Starting Import on file ' + path)

            with open(path, mode='rt') as f:
                reader = csv.reader(f, dialect='excel')

                for row in reader:
                    try:
                        building = Building.objects.get(pk=row[0])
                        building.address = row[3]
                        building.save()
                        self.stdout.write('Address: ' + building.address)
                        self.stdout.write('Updated address for ' + building.name)

                    except Building.DoesNotExist:
                        building = None
        else:
            self.stdout.write('CSV file path is required')
