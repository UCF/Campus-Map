'''
	This file is used only for testing code
	
'''
from django.core.management.base import BaseCommand
import os, campus, json
from apps.campus.models import MapObj, Group

class Command(BaseCommand):
	def handle(self, *args, **options):
		MapObj.objects.filter(abbreviation="MAP")
		MapObj.objects.filter(permit_type="Greek Row")
		