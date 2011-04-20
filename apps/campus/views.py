from django.shortcuts import render_to_response
from django.http      import HttpResponse, HttpResponseNotFound, Http404
from django.views.generic.simple import direct_to_template as render
from django.core.urlresolvers import reverse

import settings, json, re

def home(request, format=None, **kwargs):
	'''
	Renders the main google map.
	One thing that seems to be working well so far, json encoding kwargs and
	using as js options for the map, that way other views can call home and
	pass whatever map options are needed
	'''
	from time import time
	date = int(time())
		
	if format == 'json':
		from campus.templatetags.weather import weather
		campus = { 
			"name"    : "UCF Campus Map",
			"weather" : weather(json_request=True) 
		}
		
		response = HttpResponse(json.dumps(campus))
		response['Content-type'] = 'application/json'
		return response
	
	if format == 'txt':
		from campus.templatetags.weather import weather
		text = u"UCF Campus Map - %s\n%s\n\n# Campus Address\n%s\n\n# Weather\n%s" % (
				request.build_absolute_uri(reverse('home')),
				"-"*78,
				"4000 Central Florida Blvd. Orlando, Florida, 32816",
				weather(text_request=True))
				
				
		response = HttpResponse(text)
		response['Content-type'] = 'text/plain; charset=utf-8'
		return response
	
	# points on the map (will have to be extended with more data added)
	if 'points' in kwargs and kwargs['points']:
		from campus.models import Building
		buildings = Building.objects.all()
		points = {}
		for b in buildings:
			b = b.json()
			points[b['number']] = { 'gpoint' : b['googlemap_point'], 'ipoint' : b['illustrated_point'] }
		
		'''
		from django.db.models import Q
		q1 = Q(googlemap_point__isnull=True)
		q2 = Q(googlemap_point__exact='')
		q3 = Q(googlemap_point__contains='None')
		q =  (q1 | q2 | q3)
		points = Building.objects.exclude( q )
		
		
		buildings = ["union", "millican"];
		q = Q()
		for name in buildings:
			q = q | Q(name__icontains = name)
		points = Building.objects.filter( q )
		'''
	else:
		points = None
		
	# urls
	version = 15 # clears google's cache
	# TODO: https://groups.google.com/group/kml-support-getting-started/browse_thread/thread/757295a81285c8c5
	if settings.GOOGLE_CAN_SEE_ME:
		buildings_kml = "%s.kml?v=%s" % (request.build_absolute_uri(reverse('buildings')), version)
		sidewalks_kml = "%s.kml?v=%s" % (request.build_absolute_uri(reverse('sidewalks')), version)
		parking_kml   = "%s.kml?v=%s" % (request.build_absolute_uri(reverse('parking')), version)
	else:
		buildings_kml = "%s%s.kml?v=%s" % (settings.GOOGLE_LOOK_HERE, reverse('buildings'), version)
		sidewalks_kml = "%s%s.kml?v=%s" % (settings.GOOGLE_LOOK_HERE, reverse('sidewalks'), version)
		parking_kml    = "%s%s.kml?v=%s" % (settings.GOOGLE_LOOK_HERE, reverse('parking'), version)
	loc = "%s.json" % reverse('location', kwargs={'loc':'foo'})
	loc = loc.replace('foo', '%s')
	kwargs['map'] = 'gmap';
	context = {
		'options'       : json.dumps(kwargs), 
		'points'        : json.dumps(points), 
		'date'          : date,
		'buildings_kml' : buildings_kml,
		'sidewalks_kml' : sidewalks_kml,
		'parking_kml'   : parking_kml,
		'loc_url'       : loc
	}
	
	return render(request, 'campus/base.djt', context)


def buildings(request, format=None):
	
	from campus.models import Building
	buildings = Building.objects.exclude(googlemap_point__isnull=True)
	
	if format == 'json':
		arr = []
		for b in buildings:
			arr.append(b.json())
		response = HttpResponse(json.dumps(arr))
		response['Content-type'] = 'application/json'
		return response
		
	if format == 'kml':
		# helpful:
		# http://code.google.com/apis/kml/documentation/kml_tut.html#network_links
		
		def flat(l):
			'''
			TODO: move this into an abstract model
			flatten array and create a a list of coordinates separated by a space
			'''
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
		
		response = render_to_response('api/buildings.kml', { 'buildings':buildings })
		response['Content-type'] = 'application/vnd.google-earth.kml+xml'
		return response
	
	context = { 'buildings' : buildings }
	return render(request, 'campus/buildings.djt', context)

def parking(request, format=None):
	
	from campus.models import ParkingLot
	lots = ParkingLot.objects.all()
	
	if format == 'kml':
		response = render_to_response('api/parking.kml', { 'parking':lots })
		response['Content-type'] = 'application/vnd.google-earth.kml+xml'
		return response
	
	return home(request, parking=True)
	
	
def sidewalks(request, format=None):
	'''
	Mostly an API wrapper
	'''
	from campus.models import Sidewalk
	sidewalks = Sidewalk.objects.all()
	
	url = request.build_absolute_uri(reverse('sidewalks'))
	
	if format == 'kml':
		response = render_to_response('api/sidewalks.kml', { 'sidewalks':sidewalks })
		response['Content-type'] = 'application/vnd.google-earth.kml+xml'
		return response
	
	if format == 'json':
		# trying to stick to the  geojson spec: http://geojson.org/geojson-spec.html
		arr = []
		for s in sidewalks:
			sidewalk = {
				"type": "Feature", 
				"geometry": { 
					"type": "LineString", 
					"coordinates": json.loads(s.poly_coords)
				}
			}
			arr.append(sidewalk)
		obj = {
			"name"     : "UCF Sidewalks",
			"source"   : "University of Central Florida",
			"url"      : url + ".json",
			"type"     : "FeatureCollection",
			"features" : arr
		}
		response = HttpResponse(json.dumps(obj, indent=4))
		response['Content-type'] = 'application/json'
		return response
	
	if format == 'txt':
		text = "University of Central Florida\nCampus Map: Sidewalks\n%s\n%s\n" % (
					url + ".txt",
					"-"*78)
		for s in sidewalks:
			text += "\n" + s.kml_coords
		response = HttpResponse(text)
		response['Content-type'] = 'text/plain; charset=utf-8'
		return response
	
	return home(request, sidewalks=True)

def bikeracks(request, format=None):
	'''
	Mostly an API wrapper
	'''
	from campus.models import BikeRack
	bikeracks = BikeRack.objects.all()
	
	url = request.build_absolute_uri(reverse('bikeracks'))
	
	# trying to stick to the  geojson spec: http://geojson.org/geojson-spec.html
	arr = []
	for r in bikeracks:
		bikerack = {
			"type": "Feature", 
			"geometry": { 
				"type": "Point", 
				"coordinates": json.loads( "%s" % r.googlemap_point)
			}
		}
		arr.append(bikerack)
	obj = {
		"name"     : "UCF Bike Racks",
		"source"   : "University of Central Florida",
		"url"      : url + ".json",
		"type"     : "FeatureCollection",
		"features" : arr
	}
	
	if format == 'json':
		response = HttpResponse(json.dumps(obj, indent=4))
		response['Content-type'] = 'application/json'
		return response
	
	if format == 'txt':
		text = "University of Central Florida\nCampus Map: Bike Racks\n%s\n%s\n" % (
					url + ".txt",
					"-"*78)
		for r in bikeracks:
			text += "\n%*d: %s" %(2, r.id, r.googlemap_point)
		response = HttpResponse(text)
		response['Content-type'] = 'text/plain; charset=utf-8'
		return response
	
	return home(request, bikeracks=True, bikeracks_geo=obj)

def emergency_phones(request, format=None):
	'''
	Mostly an API wrapper (very similar to bike racks, probably shoudl abstract this a bit)
	'''
	from campus.models import EmergencyPhone
	phones = EmergencyPhone.objects.all()
	
	url = request.build_absolute_uri(reverse('emergency_phones'))
	
	# trying to stick to the  geojson spec: http://geojson.org/geojson-spec.html
	arr = []
	for p in phones:
		phone = {
			"type": "Feature", 
			"geometry": { 
				"type": "Point", 
				"coordinates": json.loads( "%s" % p.googlemap_point)
			}
		}
		arr.append(phone)
	obj = {
		"name"     : "UCF Emergency Phones",
		"source"   : "University of Central Florida",
		"url"      : url + ".json",
		"type"     : "FeatureCollection",
		"features" : arr
	}
	
	if format == 'json':
		response = HttpResponse(json.dumps(obj, indent=4))
		response['Content-type'] = 'application/json'
		return response
	
	if format == 'txt':
		text = "University of Central Florida\nCampus Map: Emergency Phones\n%s\n%s\n" % (
					url + ".txt",
					"-"*78)
		for p in phones:
			text += "\n%*d: %s" %(2, p.id, p.googlemap_point)
		response = HttpResponse(text)
		response['Content-type'] = 'text/plain; charset=utf-8'
		return response
	
	return home(request, emergency_phones=True, phone_geo=obj)


def location_html(loc, request):
	'''
	TODO
	This really should be a model method, but it's time to go home
	'''
	from django.template.loader import get_template
	from django.template import Context
	base_url = request.build_absolute_uri('/')[:-1]
	context  = { 'location':loc, 'base_url':base_url }
	location_type = loc.__class__.__name__.lower()
	template = 'api/info_win_%s.djt' % (location_type)
	
	# create info HTML using template
	t = get_template(template)
	c = Context({
		'location'  : loc,
		'base_url'  : base_url,
		'debug'     : settings.DEBUG,
		'MEDIA_URL' : settings.MEDIA_URL })
	return t.render(c)

def location(request, loc, format=None):
	'''
	Will one day be a wrapper for all data models, searching over all locations
	and organizations, maybe even people too
	'''
	from campus.models import Building, Location
	
	try:
		location = Building.objects.get(pk=loc)
	except Building.DoesNotExist:
		try:
			location = Location.objects.get(pk=loc)
		except Location.DoesNotExist:
			raise Http404()
	
	html = location_html(location, request)
	location = location.json()
	location['info'] = html
	base_url = request.build_absolute_uri('/')[:-1]
	location['marker'] = base_url + settings.MEDIA_URL + 'images/markers/yellow.png'
	
	if format == 'bubble':
		return render(request, template, context)
	
	if format == 'json':
		if settings.DEBUG:
			import time
			time.sleep(.5)
		
		response = HttpResponse(json.dumps(location))
		response['Content-type'] = 'application/json'
		return response
	
	return home(request, location=location)
	

def search(request, format=None):
	'''
	one day will search over all data available
	'''
	from campus.models import Building
	
	query_string = ''
	bldgs = None
	if ('q' in request.GET) and request.GET['q'].strip():
		query_string = request.GET['q']
		entry_query = get_query(query_string, ['name',])		
		bldgs = Building.objects.filter(entry_query).order_by('name')
		
	if format == 'list':
		''' used with the search ajax '''
		
		if settings.DEBUG:
			# otherwise too many/too fast, gives browser a sad
			import time
			time.sleep(.5)
		
		response = ''
		if len(bldgs) < 1:
			response = '<li><a data-pk="null">No results</a></li>'
			return HttpResponse(response)
		count = 0
		for item in bldgs:
			response += '<li>%s</li>' % (item.link)
			count += 1
			if(count > 9):
				response += '<li class="more"><a href="%s?q=%s" data-pk="more-results">More results &hellip;</a></li>' % (
					reverse('search'), query_string)
				return HttpResponse(response)
		return HttpResponse(response)
	
	if format == 'json':
		def clean(item):
			return {
				'type' : str(item.__class__.__name__),
				'name' : item.name,
				'id'   : item.pk }
		search = {
			"query"   : query_string,
			"results" : map(clean, bldgs)
		}
		response = HttpResponse(json.dumps(search))
		response['Content-type'] = 'application/json'
		return response
	
	from apps.views import phonebook_search
	phonebook = phonebook_search(query_string)
	
	found_entries = {
		'buildings' : bldgs,
		'phonebook' : phonebook['results']
	}
	
	context = {'search':True, 'query':query_string, 'results':found_entries }
	return render(request, 'campus/search.djt', context)
	


# thanks:  http://www.julienphalip.com/blog/2008/08/16/adding-search-django-site-snap/
def normalize_query(query_string,
					findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
					normspace=re.compile(r'\s{2,}').sub):
	''' 
		Splits the query string in invidual keywords, getting rid of unecessary spaces
		and grouping quoted words together.
		Example:

		>>> normalize_query('  some random	words "with	  quotes  " and	  spaces')
		['some', 'random', 'words', 'with quotes', 'and', 'spaces']	   
	'''
	return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)] 

# thanks:  http://www.julienphalip.com/blog/2008/08/16/adding-search-django-site-snap/
def get_query(query_string, search_fields):
	''' 
		Returns a query, that is a combination of Q objects. That combination
		aims to search keywords within a model by testing the given search fields.	  
	'''
	from django.db.models import Q
	query = None # Query to search for every search term		
	terms = normalize_query(query_string)
	for term in terms:
		or_query = None # Query to search for a given term in each field
		for field_name in search_fields:
			q = Q(**{"%s__icontains" % field_name: term})
			if or_query is None:
				or_query = q
			else:
				or_query = or_query | q
		if query is None:
			query = or_query
		else:
			query = query & or_query
	return query


def regional_campuses(request, campus=None, format=None):
	from campus.models import RegionalCampus
	
	# TODO - regional campuses API
	if format == 'json':
		response = HttpResponse(json.dumps("API not available for Regional Campuses"))
		response['Content-type'] = 'application/json'
		return response
	
	if format == 'txt':
		response = HttpResponse("API not available for Regional Campuses")
		response['Content-type'] = 'text/plain; charset=utf-8'
		return response
	
	if campus:
		try:
			rc = RegionalCampus.objects.get(pk=campus)
		except RegionalCampus.DoesNotExist:
			raise Http404()
		else:
			img = rc.img_tag
			rc = rc.json()
			rc['html'] = img + '<a href="%s">More info...</a>' % (reverse('regional'))
			return home(request, regional_campus=rc)
	
	campuses = RegionalCampus.objects.all()
	context = { "campuses": campuses }
	
	return render(request, 'campus/regional-campuses.djt', context)