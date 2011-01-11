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
	
	return home(request, buildings=buildings)


def search(request, format=None):
	from campus.models import Building
	query_string = ''
	found_entries = None
	if ('q' in request.GET) and request.GET['q'].strip():
		query_string = request.GET['q']
		entry_query = get_query(query_string, ['name',])		
		found_entries = Building.objects.filter(entry_query).order_by('name')
		
	if format == 'json':
		search = {
			"query"   : query_string,
			"results" : map(lambda e: e.json(), found_entries)
		}
		response = HttpResponse(json.dumps(search))
		response['Content-type'] = 'application/json'
		return response
	
	context = {'search':True, 'query':query_string, 'results':found_entries }
	return render_to_response('campus/search.djt', context)
	


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