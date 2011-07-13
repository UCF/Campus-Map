from django.shortcuts import render_to_response
from django.http      import HttpResponse, HttpResponseNotFound, Http404, HttpResponsePermanentRedirect
from django.views.generic.simple import direct_to_template as render
from django.core.urlresolvers import reverse

import settings, json, re

def home(request, **kwargs):
	'''
	Renders the main google map.
	One thing that seems to be working well so far, json encoding kwargs and
	using as js options for the map, that way other views can call home and
	pass whatever map options are needed
	'''
	from time import time
	date = int(time())
	
	
	# process query string
	loc_id = request.GET.get('show', False)
	if loc_id:
		loc = location(request, loc=loc_id, return_obj=True)
		loc.pop('profile')
		loc.pop('poly_coords')
		kwargs['location'] = loc
	
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
	if kwargs.get('points', False):
		from campus.models import Building
		buildings = Building.objects.all()
		points = {}
		for b in buildings:
			b = b.json()
			points[b['number']] = { 'gpoint' : b['googlemap_point'], 'ipoint' : b['illustrated_point'] }
	else:
		points = None
		
	# urls
	version = 16 # clears google's cache
	# TODO: https://groups.google.com/group/kml-support-getting-started/browse_thread/thread/757295a81285c8c5
	if settings.GOOGLE_CAN_SEE_ME:
		buildings_kml = "%s.kml?v=%s" % (request.build_absolute_uri(reverse('locations')), version)
		sidewalks_kml = "%s.kml?v=%s" % (request.build_absolute_uri(reverse('sidewalks')), version)
		parking_kml   = "%s.kml?v=%s" % (request.build_absolute_uri(reverse('parking')), version)
	else:
		buildings_kml = "%s%s.kml?v=%s" % (settings.GOOGLE_LOOK_HERE, reverse('locations'), version)
		sidewalks_kml = "%s%s.kml?v=%s" % (settings.GOOGLE_LOOK_HERE, reverse('sidewalks'), version)
		parking_kml    = "%s%s.kml?v=%s" % (settings.GOOGLE_LOOK_HERE, reverse('parking'), version)
	loc = "%s.json" % reverse('location', kwargs={'loc':'foo'})
	loc = loc.replace('foo', '%s')
	kwargs['map'] = 'gmap';
	
	error = kwargs.get('error', None)
	if error:
		kwargs.pop('error')
	
	context = {
		'options'       : json.dumps(kwargs), 
		'points'        : json.dumps(points), 
		'date'          : date,
		'buildings_kml' : buildings_kml,
		'sidewalks_kml' : sidewalks_kml,
		'parking_kml'   : parking_kml,
		'loc_url'       : loc,
		'base_url'      : request.build_absolute_uri(reverse('home'))[:-1],
		'error'         : error,
	}
	
	return render(request, 'campus/base.djt', context)


def locations(request):
	
	from campus.models import Building, Location, RegionalCampus, Group
	buildings = Building.objects.all()
	locations = Location.objects.all()
	campuses  = RegionalCampus.objects.all()
	groups    = Group.objects.all()
	
	if request.is_json():
		arr = []
		for b in buildings:
			arr.append(b.json())
		response = HttpResponse(json.dumps(arr))
		response['Content-type'] = 'application/json'
		return response
		
	if request.is_kml():
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
	
	context = { 
		'buildings' : buildings,
		'locations' : locations,
		'campuses'  : campuses,
		'groups'    : groups
	}
	return render(request, 'campus/locations.djt', context)

def location(request, loc, return_obj=False):
	'''
	Will one day be a wrapper for all data models, searching over all locations
	and organizations, maybe even people too
	'''
	from campus.models import Building, Location
	
	
	location_orgs = []
	try:
		location = Building.objects.get(pk=loc)
		location_orgs = location._orgs(limit=-1)['results']
	except Building.DoesNotExist:
		try:
			location = Location.objects.get(pk=loc)
		except Location.DoesNotExist:
			raise Http404("Location ID <code>%s</code> could not be found" % (loc))
	
	location_type = location.__class__.__name__
	html = location_html(location, request)
	location = location.json()
	location['info'] = html
	base_url = request.build_absolute_uri('/')[:-1]
	location['marker'] = base_url + settings.MEDIA_URL + 'images/markers/yellow.png'
	
	# API views
	if request.is_json():
		if settings.DEBUG:
			import time
			time.sleep(.5)
		response = HttpResponse(json.dumps(location))
		response['Content-type'] = 'application/json'
		return response
	
	org = None
	if request.GET.get('org', None):
		from apps.views import get_org
		org = get_org(request.GET['org'])
	
	if return_obj:
		return location
	elif location_type == "Building":
		# show location profile
		
		import flickr
		photos = flickr.get_photos()
		tags = set()
		if 'id' in location:
			tags.add( 'map%s' % location['id'].lower() )
		if 'abbreviation' in location:
			tags.add( 'map%s' % location['abbreviation'].lower() )
		if 'number' in location:
			tags.add( 'map%s' % location['number'].lower() )
		for p in list(photos):
			ptags = set(p.tags.split(' ')).intersection(tags)
			if(not bool(ptags)):
				photos.remove(p)
			else:
				p.info = '<h2><a href="http://flickr.com/photos/universityofcentralflorida/%s/">%s</a></h2>' % (p.id, p.title)
				if p.description.text:
					p.info = "%s<p>%s</p>" % (p.info, p.description.text)
		
		context = { 
			'location' : location,
			'orgs'     : location_orgs,
			'org'      : org,
			'photos'   : photos,
		}
		return render(request, 'campus/location.djt', context)
	else:
		# show location on the map
		return home(request, location=location)

def parking(request):
	
	from campus.models import ParkingLot
	lots = ParkingLot.objects.all()
	
	if request.is_kml():
		response = render_to_response('api/parking.kml', { 'parking':lots })
		response['Content-type'] = 'application/vnd.google-earth.kml+xml'
		return response
	
	return home(request, parking=True)
	
	
def sidewalks(request):
	'''
	Mostly an API wrapper
	'''
	from campus.models import Sidewalk
	sidewalks = Sidewalk.objects.all()
	
	url = request.build_absolute_uri(reverse('sidewalks'))
	
	if request.is_kml():
		response = render_to_response('api/sidewalks.kml', { 'sidewalks':sidewalks })
		response['Content-type'] = 'application/vnd.google-earth.kml+xml'
		return response
	
	if request.is_json():
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
	
	if request.is_txt():
		text = "University of Central Florida\nCampus Map: Sidewalks\n%s\n%s\n" % (
					url + ".txt",
					"-"*78)
		for s in sidewalks:
			text += "\n" + s.kml_coords
		response = HttpResponse(text)
		response['Content-type'] = 'text/plain; charset=utf-8'
		return response
	
	return home(request, sidewalks=True)

def bikeracks(request):
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
	
	if request.is_json():
		response = HttpResponse(json.dumps(obj, indent=4))
		response['Content-type'] = 'application/json'
		return response
	
	if request.is_txt():
		text = "University of Central Florida\nCampus Map: Bike Racks\n%s\n%s\n" % (
					url + ".txt",
					"-"*78)
		for r in bikeracks:
			text += "\n%*d: %s" %(2, r.id, r.googlemap_point)
		response = HttpResponse(text)
		response['Content-type'] = 'text/plain; charset=utf-8'
		return response
	
	return home(request, bikeracks=True, bikeracks_geo=obj)

def emergency_phones(request):
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
	
	if request.is_json():
		response = HttpResponse(json.dumps(obj, indent=4))
		response['Content-type'] = 'application/json'
		return response
	
	if request.is_txt():
		text = "University of Central Florida\nCampus Map: Emergency Phones\n%s\n%s\n" % (
					url + ".txt",
					"-"*78)
		for p in phones:
			text += "\n%*d: %s" %(2, p.id, p.googlemap_point)
		response = HttpResponse(text)
		response['Content-type'] = 'text/plain; charset=utf-8'
		return response
	
	return home(request, emergency_phones=True, phone_geo=obj)


def location_html(loc, request, orgs=True):
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
		'orgs'      : orgs,
		'base_url'  : base_url,
		'debug'     : settings.DEBUG,
		'MEDIA_URL' : settings.MEDIA_URL })
	return t.render(c)

def backward_location(request):
	'''
	Wraps location view to enable backwards compatibility with old campus
	map URLs.
	Example: http://campusmap.ucf.edu/flash/index.php?select=b_8118
	'''
	
	select = request.GET.get('select', None)
	
	if select is not None:
		match = re.search('b_(\d+)', select)
		if match is not None:
			url = reverse('location', kwargs={'loc':match.groups()[0]})
			return HttpResponsePermanentRedirect(url)
	raise Http404()
	
def regional_campuses(request, campus=None):
	from campus.models import RegionalCampus
	
	# TODO - regional campuses API
	if request.is_json():
		response = HttpResponse(json.dumps("API not available for Regional Campuses"))
		response['Content-type'] = 'application/json'
		return response
	
	if request.is_txt():
		response = HttpResponse("API not available for Regional Campuses")
		response['Content-type'] = 'text/plain; charset=utf-8'
		return response
	
	if campus:
		try:
			rc = RegionalCampus.objects.get(pk=campus)
		except RegionalCampus.DoesNotExist:
			raise Http404()
		else:
			html = location_html(rc, request, orgs=False)
			img = rc.img_tag
			rc = rc.json()
			rc['info'] = html
			return home(request, location=rc)
	
	campuses = RegionalCampus.objects.all()
	context = { "campuses": campuses }
	
	return render(request, 'campus/regional-campuses.djt', context)

def data_dump(request):
	from django.core import serializers
	from django.db.models import get_apps
	from django.core.management.commands.dumpdata import sort_dependencies
	from django.utils.datastructures import SortedDict
	import campus
	
	app = campus
	app_list = SortedDict([(app, None) for app in get_apps()])
	
	# Now collate the objects to be serialized.
	objects = []
	for model in sort_dependencies(app_list.items()):
		objects.extend(model.objects.all())
	
	try:
		data = serializers.serialize('json', objects, indent=4)
	except Exception, e:
		data = serializers.serialize('json', "ERORR!")
	
	response = HttpResponse(data)
	response['Content-type'] = 'application/json'
	return response
	
	
	
