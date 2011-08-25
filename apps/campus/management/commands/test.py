'''
	This file is used *only* for testing code
	Feel free to destroy / overwrite anything and use as a sandbox
'''
from django.core.management.base import BaseCommand
class Command(BaseCommand):
	def handle(self, *args, **options):
		from apps.campus.models import MapObj, Building
		from django.db.models import Q
		
		
		q1 = Q(name__icontains='commons')
		q2 = Q(abbreviation__icontains='map')
		
		print MapObj.objects.filter(q1|q2)
		
		