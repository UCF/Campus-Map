from django.http      import HttpResponse, Http404
from django.views.generic.simple import direct_to_template as render
from django.template import TemplateDoesNotExist

from django.core.cache import cache
import settings, urllib, json, re

def pages(request, page=None, format=None):
	'''
	static pages with API placeholders
	'''
	if format == 'json':
		import json
		response = HttpResponse(json.dumps('Not this page silly!'))
		response['Content-type'] = 'application/json'
		return response
	
	if format == 'txt':
		response = HttpResponse('Not this page silly!')
		response['Content-type'] = 'text/plain; charset=utf-8'
		return response
	
	try:
		return render(request, "pages/%s.djt" % page, { 'page' : page })
	except TemplateDoesNotExist:
		raise Http404()


def organizations(request, format=None):
	context = {'organizations': get_orgs() }
	return render(request, "pages/organizations.djt", context)

def organization(request, id, format=None):
	org = get_org(id)
	building = None
	try:
		from campus.models import Building
		building = Building.objects.get(pk=org['bldg_id'])
		from campus.views import location_html
		# TODO: make this a model method
		building_html = location_html(building, request)
	except Building.DoesNotExist:
		pass
	context = {'org': org, 'building':building, 'building_html': building_html }
	return render(request, "pages/organization.djt", context)


def get_orgs():
	orgs = cache.get('organizations')
	if orgs is None:
		url = settings.PHONEBOOK + '?use=tableSearch&in=organizations&order_by=name&order=ASC'
		try:
			results = urllib.urlopen(url).read()
			orgs = json.loads(results)
		except:
			print "Issue with phonebook search service"
			return None
		else:
			cache.set('organizations', orgs)
	return orgs

def get_depts():
	depts = cache.get('departments')
	if depts is None:
		url = settings.PHONEBOOK + '?use=tableSearch&in=departments&order_by=name&order=ASC'
		try:
			results = urllib.urlopen(url).read()
			depts = json.loads(results)
		except:
			print "Issue with phonebook search service"
			return None
		else:
			cache.set('departments', depts)
	return depts

def get_org(id):
	orgs = get_orgs()
	for o in orgs['results']:
		if o['id'] == id:
			depts = get_depts()
			o['departments'] = []
			for d in depts['results']:
				if d['org_id'] == id and d['name'] is not None:
					o['departments'].append(d)
			return o

def phonebook_search(q):
	url = "%s?search=%s" % (settings.PHONEBOOK, q)
	try:
		results = urllib.urlopen(url).read()
		return json.loads(results)
	except:
		print "Issue with phonebook search service"
		return None

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