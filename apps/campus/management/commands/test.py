'''
	This file is used only for testing code
	
'''
from django.core.management.base import BaseCommand
import os, campus, json
from apps.campus.models import MapObj, Group
from django.core.management import call_command
import StringIO, sys
from django.db.models import Q

class Command(BaseCommand):
	def handle(self, *args, **options):
		print "oh yeah"
		
		print 
		for o in MapObj.objects.mob_filter(Q()):
			print type(o)