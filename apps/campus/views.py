from django.shortcuts import render_to_response
from django.http      import HttpResponse, HttpResponseNotFound
from django.views.generic.simple import direct_to_template as render
from django.core.urlresolvers import reverse

import settings

def home(request, format=None, **kwargs):
	from time import time
	date = int(time())
		
	if format == 'json':
		import json
		from campus.templatetags.weather import weather
		campus = { 
			"name"    : "UCF Campus Map",
			"weather" : weather(json_request=True) 
		}
		
		response = HttpResponse(json.dumps(campus))
		response['Content-type'] = 'application/json'
		return response
	
	if settings.GOOGLE_CAN_SEE_ME:
		kml = "%s.kml" % (request.build_absolute_uri(reverse('buildings')))
	else:
		kml = "%s%s.kml" % (settings.GOOGLE_LOOK_HERE, reverse('buildings'))
	
	return render(request, 'campus/base.djt', { 'date':date, 'options': kwargs, 'kml':kml })



def buildings(request, format=None):
	
	from campus.models import Building
	buildings = Building.objects.exclude(googlemap_point__isnull=True)
	# from django.db.models import Q
	# buildings = Building.objects.exclude( Q(googlemap_point__isnull=True) | Q(googlemap_point__exact='') | Q(googlemap_point__contains='None') )
	
	if format == 'json':
		import json
		arr = []
		for b in buildings:
			arr.append(b.json())
		response = HttpResponse(json.dumps(arr))
		response['Content-type'] = 'application/json'
		return response
		
	if format == 'kml':
		# helpful:
		# http://code.google.com/apis/kml/documentation/kml_tut.html#network_links
		import json
		
		def flat(l):
			'''flatten array and create a a list of coordinates separated by a space'''
			str = ""
			for i in l:
				if type(i[0]) == type([]):
					return flat(i)
				else:
					str += ("%.6f,%.6f ")  % (i[0], i[1])
			return str
		
		for b in buildings:
			if b.poly_coords != None:
				arr = json.loads(b.poly_coords)
				kml_string = flat(arr)
				b.poly_coords = kml_string
		
		response = render_to_response('campus/buildings.kml', { 'buildings':buildings })
		response['Content-type'] = 'application/vnd.google-earth.kml+xml'
		return response
	
	return home(request, buildings=buildings)