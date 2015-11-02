import json
import os.path
import re
import StringIO
import sys
import warnings

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.models.query import QuerySet
from django.db import connection, transaction
from django.db.utils import IntegrityError, DatabaseError

from campus.admin import create_groupable_locations
from campus.models import Group, GroupedLocation, MapObj, DiningLocation
import campus

try:
    from _mysql_exceptions import OperationalError
except ImportError:
    class OperationalError: pass


class Command(BaseCommand):
    args = 'none'
    help = 'load all campus fixtures'

    def run_query(self, sql):
        cursor = connection.cursor()
        error = False
        for l in sql.split("\n"):
            if not l: continue
            if l.count('COMMIT'): continue
            try:
                cursor.execute(l)
            except (OperationalError,IntegrityError) as e:
                error = e
            except DatabaseError:
                pass # "unknown table, happens on second pass"
        return error

    def table_names(self):

        cursor = connection.cursor()
        try:
            # mysql
            campus_tables = "SELECT table_name \
                    FROM INFORMATION_SCHEMA.TABLES \
                    WHERE table_schema='%s' \
                    AND (LOCATE('campus_', table_name) = 1 OR LOCATE('south_', table_name) = 1)" % settings.DATABASES['default']['NAME']
            cursor.execute(campus_tables)
            return cursor
        except DatabaseError:
            pass

        try:
            # sqlite
            campus_tables = "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND (name LIKE 'campus_%%' OR name LIKE 'south_%%')"
            cursor.execute(campus_tables)
            return cursor
        except DatabaseError:
            pass

        raise DatabaseError('Can not read table names from the database')

    def reset_sql(self):
        tables = self.table_names()

        sql = 'SET FOREIGN_KEY_CHECKS=0;\n'
        for name in tables:
            sql += "DROP TABLE `%s`;\n" % name
        sql += 'SET FOREIGN_KEY_CHECKS=1;\n'
        return sql

    def handle(self, *args, **options):

        print "Crunching datas:"

        '''
        Reset Campus
        "manage.py reset" has been woefull deprecated, so no:
        call_command('reset', 'campus', verbosity=0, interactive=False)

        Ran into issue with Windows
        The SQL generated from sqlclear always failed (an issue with the names
        of foriegn key constraints).  If the SQL is ran twice, the tables with
        dependencies will be removed first and independent tables removed second

        Future compatibility issues:
        sqlclear and reset both generate sql based on models in the project.
        Sometimes we have to jump back/forth between map versions and the
        models/tablenames between the two are not yet knows.  The sql is now
        generated directly from in information schema

        Noreset argument allows to run the campusdata command
        without data being removed
        '''
        noreset = "noreset" in args

        if noreset == True:
            print "Database will not be reset."
        else:
            for i in range(2):
                sql = self.reset_sql()
                error = self.run_query(sql)
            if error:
                print "Failed to update the db :("
                print type(error)
                print error
                return

        #syncdb
        call_command('syncdb', verbosity=0, interactive=False)

        #south migrate
        if options.get('test') is not True:
            call_command('migrate', verbosity=0, interactive=False)

        # load all the data from fixtures
        path = os.path.join(os.path.dirname(campus.__file__), 'fixtures')
        fixtures = os.listdir(path)
        fixtures.sort()
        for f in fixtures:
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
        print "  Updating groups ..."
        with open(os.path.join(path, 'groups.json'), 'r') as f: txt = f.read()
        groups = json.loads(txt)
        for g in groups[:]:
            locations = g['fields'].pop('locations')
            qs = QuerySet(MapObj)
            mob = qs.get(id=g['pk'])
            mob = mob.__dict__
            mob.pop('_state')

            if noreset:
                obj, created = Group.objects.get_or_create(**mob)

            else:
                Group.objects.create(**mob)

            '''
            when / if groups get additional attributes, will have to extend importer here
            for k,v in g['fields']:
                setattr(new, k, v)
            '''
            g['fields']['locations'] = locations

        sys.stdout.write("  Updating content types ")
        create_groupable_locations(verbosity=1)
        sys.stdout.flush()
        print

        # Create/Update DiningLocations from search service
        print '  Updating dining ...'
        DiningLocation.refresh()

        sys.stdout.write("  Updating m2m locations ")
        for g in groups[:]:
            group     = Group.objects.get(id = g['pk'])
            locations = g['fields']['locations']
            count = 0
            for l in locations:
                gl = GroupedLocation.objects.get_by_natural_key(l[0], l[1])
                group.locations.add(gl)

                # too many dots, otherwise
                if count % 3 == 0:
                    sys.stdout.write(".")
                    sys.stdout.flush()
                count = count +1

        print "All done. The map nom'd all the data and is happy."
