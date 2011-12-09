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
		
		from campus.models import DisabledParking
		import re
		dp = DisabledParking.objects.all()
		counter = 0
		for p in dp:
			counter += 1
			id = p.id
			p.description = p.name
			m = re.match(r"(?P<desc>.+) \((?P<num>\d+).*", p.description)
			if m:
				p.description = m.group('desc')
				p.num_spaces = m.group('num')
				
			p.id = "disabledparking-%0.3d" % counter
			p.name = None
			p.save()
			p = DisabledParking.objects.get(id=id)
			p.delete()