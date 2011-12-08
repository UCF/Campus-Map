'''
	This file is used only for testing code.
	to use, in your Campus Map project:
		python manage.py test
	
'''
from django.core.management.base import BaseCommand
import os, campus, json
from apps.campus.models import MapObj
from django.core.management import call_command

def prompt():
	''' keep me, I'm useful '''
	while(True):
		i = raw_input("Accept? [y/n] ")
		if(i == 'y'): 
			print
			return True
		elif(i == 'n'): 
			print
			return False
		else: 
			print "what?"

class Command(BaseCommand):
	
	def handle(self, *args, **options):
		'''
		From here down
		Feel free to overwrite, delete, or change anything
		
		'''
		
		import settings
		from django.db import connection, transaction
		cursor = connection.cursor()
		print cursor.description
		sql = "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name LIKE 'campus_%%'"
		print sql
		cursor.execute(sql)
		print cursor.description
		for r in cursor:
			print r