'''
	This file is used only for testing code
	
'''
from django.core.management.base import BaseCommand
import os, campus, json
from apps.campus.models import MapObj
from django.core.management import call_command

class Command(BaseCommand):
	def handle(self, *args, **options):
		
		o = MapObj.objects.get(id=1)
		print o.profile_link