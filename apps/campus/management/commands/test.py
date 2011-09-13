'''
	This file is used only for testing code
	
'''
from django.core.management.base import BaseCommand
import os, campus, json
from apps.campus.models import MapObj
from django.core.management import call_command

def prompt():
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
		
		for o in MapObj.objects.all():
			if o.image:
				print "%25s" % o.image
