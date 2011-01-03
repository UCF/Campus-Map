from django.shortcuts import render_to_response
import settings
from django.db.models import Q

def home(request):
	from campus.models import Building
	from time import time
	date = int(time())
	buildings = Building.objects.exclude( Q(googlemap_point__isnull=True) )
	# buildings = Building.objects.exclude( Q(googlemap_point__isnull=True) | Q(googlemap_point__exact='') | Q(googlemap_point__contains='None') )
	return render_to_response('campus/base.djt', { 'buildings':buildings, 'date':date, 'MEDIA_URL' : settings.MEDIA_URL })

