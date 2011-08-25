'''
	This file is used only for testing code
	
'''
from django.core.management.base import BaseCommand
import os, campus, json
from apps.campus.models import MapObj, Group

from django.db import connection, transaction
from django.core.management import call_command
import StringIO, sys



class Command(BaseCommand):
	def handle(self, *args, **options):
		cursor = connection.cursor()
		output = StringIO.StringIO()
		sys.stdout = output
		call_command('sqlclear', 'campus')
		sys.stdout = sys.__stdout__
		cursor.execute(output.getvalue())
		transaction.commit()
		