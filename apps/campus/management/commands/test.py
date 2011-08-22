'''
	This file is used only for testing code
	
'''
from django.core.management.base import BaseCommand
import os, campus, json
from apps.campus.models import MapObj, Group

class Command(BaseCommand):
	def handle(self, *args, **options):
		print MapObj.objects.get(pk="1")
		print MapObj.objects.filter(abbreviation="MAP")
		print MapObj.objects.filter(permit_type="Greek Row")
		