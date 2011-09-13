from django.shortcuts import render_to_response, get_object_or_404
from django.http      import HttpResponse, HttpResponseNotFound, Http404, HttpResponsePermanentRedirect
from django.views.generic.simple import direct_to_template as render
from django.core.urlresolvers import reverse
from campus.models import MapObj
from django.core.cache import cache
from xml.etree import ElementTree

import settings, json, re, urllib

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
	
	if request.is_json():
		from campus.templatetags.weather import weather
		campus = { 
			"name"    : "UCF Campus Map",
			"weather" : weather(json_request=True) 
		}
		response = HttpResponse(json.dumps(campus))
		response['Content-type'] = 'application/json'
		return response
	
	if request.is_txt():
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
		from django.contrib.contenttypes.models import ContentType
		from models import Building, Location, Group, ParkingLot
		
		# Filter home page locations to building, locations, and groups
		points = cache.get('home_points')
		if points is None:
			show   = map(lambda c: ContentType.objects.get_for_model(c), (Building, Location, Group, ParkingLot))
			mobs   = MapObj.objects.filter(content_type__in=map(lambda c: c.id, show))
			points = {}
			for o in mobs:
				o = o.json()
				points[o['id']] = {
					'name'   : o['name'],
					'gpoint' : o['googlemap_point'],
					'ipoint' : o['illustrated_point'],
					'type'   : o['object_type'],
				}
			cache.set('home_points', points, 60 * 60 * 24)
	else:
		points = None
		
	# urls
	version = 18 # clears google's cache
	# TODO: https://groups.google.com/group/kml-support-getting-started/browse_thread/thread/757295a81285c8c5
	if settings.GOOGLE_CAN_SEE_ME:
		buildings_kml = "%s.kml?v=%s" % (request.build_absolute_uri(reverse('locations')[:-1]), version)
		sidewalks_kml = "%s.kml?v=%s" % (request.build_absolute_uri(reverse('sidewalks')[:-1]), version)
		parking_kml   = "%s.kml?v=%s" % (request.build_absolute_uri(reverse('parking')[:-1]), version)
	else:
		buildings_kml = "%s%s.kml?v=%s" % (settings.GOOGLE_LOOK_HERE, reverse('locations')[:-1], version)
		sidewalks_kml = "%s%s.kml?v=%s" % (settings.GOOGLE_LOOK_HERE, reverse('sidewalks')[:-1], version)
		parking_kml    = "%s%s.kml?v=%s" % (settings.GOOGLE_LOOK_HERE, reverse('parking')[:-1], version)
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
		'parking_json'  : reverse('parking') + '.json',
		'loc_url'       : loc,
		'base_url'      : request.build_absolute_uri(reverse('home'))[:-1],
		'error'         : error,
	}
	
	return render(request, 'campus/base.djt', context)


def locations(request):
	from campus.models import MapObj
	
	locations = MapObj.objects.all()
	base_url  = request.build_absolute_uri(reverse('home'))[:-1]
	
	if request.is_json():
		arr = []
		for l in locations:
			arr.append(l.json(base_url=base_url))
		response = HttpResponse(json.dumps(arr))
		response['Content-type'] = 'application/json'
		return response
		
	if request.is_kml():
		# helpful:
		# http://code.google.com/apis/kml/documentation/kml_tut.html#network_links
		response = cache.get('kml_response')
		if response is None:
			response = render_to_response('api/buildings.kml', { 'locations':locations })
			response['Content-type'] = 'application/vnd.google-earth.kml+xml'
			cache.set('kml_response', response, 60 * 60 * 24)
		return response
	
	if request.is_bxml():
		xml_locations = ElementTree.Element('Locations')
		for location in list(l.bxml for l in locations):
			xml_locations.append(location)
		response = HttpResponse(ElementTree.tostring(xml_locations,encoding='UTF-8'))
		response['Content-type'] = 'application/xml'
		return response
	
	context = cache.get('locations_context')
	if context is None:
		context = {
			'buildings' : list(),
			'locations' : list(),
			'campuses'  : list(),
			'groups'    : list(),
		}
	
		for l in locations:
			if (l.object_type == 'Building'):
				context['buildings'].append(l)
			elif(l.object_type == 'Location'):
				context['locations'].append(l)
			elif(l.object_type == 'RegionalCampus'):
				context['campuses'].append(l)
			elif(l.object_type == 'Group'):
				context['groups'].append(l)
		
		cache.set('locations_context', context, 60 * 60 * 24)
	
	return render(request, 'campus/locations.djt', context)

def location(request, loc, return_obj=False):
	'''
	Will one day be a wrapper for all data models, searching over all locations
	and organizations, maybe even people too
	'''
	
	location_orgs = []
	try:
		location = MapObj.objects.get(pk=loc)
		location_orgs = location._orgs()['results']
	except MapObj.DoesNotExist:
		raise Http404("Location ID <code>%s</code> could not be found" % (loc))
	
	base_url = request.build_absolute_uri(reverse('home'))[:-1]
	html = location_html(location, request)
	location = location.json(base_url=base_url)
	location['info'] = html
	
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
	
	# find organizations related to this location via the group it belongs to
	from models import GroupedLocation
	from django.contrib.contenttypes.models import ContentType
	
	location_ctype = ContentType.objects.get(
		app_label="campus",
		model=location['object_type'].lower()
	)
	location_pk       = location['id']
	
	# Find all groups this location is a member of
	grouped_locations = GroupedLocation.objects.filter(
		object_pk=location_pk,
		content_type=location_ctype
	)
	groups = [gl.group_set.all() for gl in grouped_locations]
	groups = reduce(lambda a, b: a + b, groups)
	
	# Find the union of all organizations between this group and its members
	def group_orgs(g):
		group_orgs = g._orgs()['results']
		orgs = [gl.content_object._orgs()['results'] for gl in g.locations.all()]
		orgs = reduce(lambda a, b: a + b, orgs) + group_orgs
		return orgs
	
	# Attach org info to each group for this location
	groups_orgs = list()
	for g in groups:
		groups_orgs.append((g, group_orgs(g)))
	
	context = { 
		'location'      : location,
		'orgs'          : location_orgs,
		'groups_orgs'   : groups_orgs,
		'org'           : org,
		'photos'        : photos,
	}
	return render(request, 'campus/location.djt', context)

def parking(request):
	from campus.models import ParkingLot, HandicappedParking
	lots     = list(ParkingLot.objects.all())
	handicap = list(HandicappedParking.objects.all())
	
	if request.is_json():
		lots     = [l.json() for l in lots]
		handicap = [h.json() for h in handicap]
		
		response = HttpResponse(json.dumps({
			'lots'     : lots,
			'handicap' : handicap,
		}))
		response['Content-type'] = 'application/json'
		return response
	
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
	base_url = request.build_absolute_uri(reverse('home'))[:-1]
	context  = { 'location':loc, 'base_url':base_url }
	location_type = loc.__class__.__name__.lower()
	template = 'api/info_win_%s.djt' % (location_type)
	group = { "overflow" : False, "locations" : False }
	if location_type == 'group':
		group['locations'] = []
		count = 0
		for gl in loc.locations.all():
			group['locations'].append(gl.content_object)
			count += 1
			if count == 4:
				group['overflow'] = True
				break
	
	# create info HTML using template
	t = get_template(template)
	c = Context({
		'location'  : loc,
		'orgs'      : orgs,
		'group'     : group,
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
	
	if select is not None and select.startswith('b_') and len(select) > 2:
		url = '?'.join([reverse('home'), urllib.urlencode({'show':select[2:]})])
		return HttpResponsePermanentRedirect(url)
	return HttpResponsePermanentRedirect(reverse('home'))
	
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
	from django.db.models import get_apps, get_app
	from django.core.management.commands.dumpdata import sort_dependencies
	from django.utils.datastructures import SortedDict
	import campus
	
	if not request.user.is_authenticated() or not request.user.is_superuser:
		response = HttpResponse(json.dumps({"Error": "Not Authorized"}))
		response['Content-type'] = 'application/json'
		return response
	
	#if wanted all apps, but only want campus
	#app_list = SortedDict([(app, None) for app in get_apps()])
	app_list = SortedDict([(get_app('campus'), None)])
	
	# Now collate the objects to be serialized.
	objects = []
	
	# Needed because sqllite doesn't use 
	def ordering(self):
		if hasattr(self, 'name'):
			return str(self.name).lower()
		elif hasattr(self, 'id'):
			return self.id
		else:
			return self.pk
	
	for model in sort_dependencies(app_list.items()):
		# skip groupedlocation model (not needed since Group uses natural keys)
		if model == campus.models.GroupedLocation:
			continue
		# - make ordering case insensitive
		# - must also make special case for MapObj else the leaf class will be
		#   serialized, not the actual MapObj itself
		if model == campus.models.MapObj:
			objects.extend( sorted(model.objects.mob_filter(), key=ordering) )
		else:
			objects.extend( sorted(model.objects.all(), key=ordering) )
	try:
		data = serializers.serialize('json', objects, indent=4, use_natural_keys=True)
	except Exception, e:
		data = serializers.serialize('json', "ERORR!")
	
	response = HttpResponse(data)
	response['Content-type'] = 'application/json'
	return response
