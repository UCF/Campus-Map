'''
	This file is used only for testing code
	
'''
from django.core.management.base import BaseCommand
import os, campus, json
from apps.campus.models import MapObj, Group
o.core.management import call_command
import StringIO, sys

class Command(BaseCommand):
	def handle(self, *args, **options):
		print "oh yeah"
		