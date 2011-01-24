from django.shortcuts import render_to_response
from django.http      import HttpResponse, HttpResponseNotFound
from django.views.generic.simple import direct_to_template as render
from django.core.urlresolvers import reverse

import settings, json, re

def home(request, format=None, **kwargs):
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
	
	# points on the map (will have to be extended with more data added)
	if 'points' in kwargs and kwargs['points']:
		from campus.models import Building
		from django.db.models import Q
		q1 = Q(googlemap_point__isnull=True)
		q2 = Q(googlemap_point__exact='')
		q3 = Q(googlemap_point__contains='None')
		q =  (q1 | q2 | q3)
		points = Building.objects.exclude( q )
		
		'''
		buildings = ["union", "millican"];
		q = Q()
		for name in buildings:
			q = q | Q(name__icontains = name)
		points = Building.objects.filter( q )
		'''
	else:
		points = None
		
	# urls
	if settings.GOOGLE_CAN_SEE_ME:
		kml = "%s.kml" % (request.build_absolute_uri(reverse('buildings')))
	else:
		kml = "%s%s.kml" % (settings.GOOGLE_LOOK_HERE, reverse('buildings'))
	loc = "%s.json" % reverse('location', kwargs={'loc':'foo'})
	loc = loc.replace('foo', '%s');
	context = { 
		'options' : kwargs, 
		'points'  : points, 
		'date'    : date,
		'kml_url' : kml,
		'loc_url' : loc
	}
	
	
	return render(request, 'campus/base.djt', context)

def organizations(request, format=None):
	
	if format == 'json':
		response = HttpResponse("org data coming soon!")
		response['Content-type'] = 'application/json'
		return response
	
	return render(request, 'campus/organizations.djt')
	

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
		
		response = render_to_response('api/buildings.kml', { 'buildings':buildings })
		response['Content-type'] = 'application/vnd.google-earth.kml+xml'
		return response
	
	context = { 'buildings' : buildings }
	return render(request, 'campus/buildings.djt', context)


def location(request, loc, format=None):
	'''
	Will one day be a wrapper for all data models, searching over all locations
	and organizations, maybe even people too
	'''
	from campus.models import Building
	try:
		location = Building.objects.get(pk=loc)
	except Building.DoesNotExist:
		location = None
	
	base_url = request.build_absolute_uri('/')[:-1]
	context  = { 'location':location, 'base_url':base_url }
	
	if format == 'bubble':
		return render(request, 'api/google_info_win.djt', context)
	
	if format == 'json':
		from django.template import Context
		from django.template.loader import get_template
		
		if settings.DEBUG:
			import time
			time.sleep(.5)
		
		t = get_template('api/google_info_win.djt')
		c = Context({
			'location'  : location,
			'base_url'  : base_url,
			'debug'     : settings.DEBUG,
			'MEDIA_URL' : settings.MEDIA_URL })
		info = t.render(c)
		if location:
			location = location.json()
			location['info'] = info
			location['marker'] = base_url + settings.MEDIA_URL + 'images/markers/yellow.png'
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
	found_entries = None
	if ('q' in request.GET) and request.GET['q'].strip():
		query_string = request.GET['q']
		entry_query = get_query(query_string, ['name',])		
		found_entries = Building.objects.filter(entry_query).order_by('name')
		
	if format == 'list':
		''' used with the search ajax '''
		
		if settings.DEBUG:
			# otherwise too many/too fast, gives browser a sad
			import time
			time.sleep(.5)
		
		response = ''
		if len(found_entries) < 1:
			response = '<li><a data-pk="null">No results</a></li>'
			return HttpResponse(response)
		count = 0
		for item in found_entries:
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
			"results" : map(clean, found_entries)
		}
		response = HttpResponse(json.dumps(search))
		response['Content-type'] = 'application/json'
		return response
	
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