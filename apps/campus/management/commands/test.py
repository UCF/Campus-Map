'''
	This file is used only for testing code
	
'''
from django.core.management.base import BaseCommand
import os, campus, json
from apps.campus.models import ParkingLot
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
		
		for p in ParkingLot.objects.all():
			
			print p.id
			
			'''
			if p.id != p.id.lower():
				
				old_id = p.id
				p.id = p.id.lower()
				p.save()
				old = ParkingLot.objects.get(id=old_id)
				old.delete()
			'''