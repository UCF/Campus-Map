from django.http      import HttpResponse, Http404
from django.views.generic.simple import direct_to_template as render
from django.template import TemplateDoesNotExist
from django.core.urlresolvers import reverse, resolve, Resolver404
from django.core.cache import cache
from django.db.models import Q
from django.utils.html import strip_tags
import settings, urllib, json, re, logging, hashlib

logger = logging.getLogger(__name__)

def page_not_found(request, **kwargs):
	from django.http import HttpResponseNotFound
	from campus.views import home
	import sys, json
	
	# from conover: exc_class, exc, traceback = sys.exc_info()
	error = sys.exc_value
	
	if len(error.args):
		error = error.args[0]
	if hasattr(error, 'get'):
		 error = "<code>%s</code> could not be found." % (error.get('path', request.path))
	if not isinstance(error, unicode):
		error = error.__unicode__()
	if not bool(error):
		error = "<code>%s</code> could not be found." % (request.path)
	
	if request.is_json():
		msg = { "error" : strip_tags(error) }
		response = HttpResponseNotFound(json.dumps(msg))
		response['Content-type'] = 'application/json'
		return response
	
	if request.is_txt():
		msg = "404 Not Found:\n%s" % strip_tags(error)
		response = HttpResponseNotFound(msg)
		response['Content-type'] = 'text/plain; charset=utf-8'
		return response
	
	request.GET ={} # must clear query string
	html = home(request, points=True, error=error)
	return HttpResponseNotFound(html)

def server_error(request, **kwargs):
	from django.http import HttpResponseServerError
	from django.conf import settings
	from django.template import Context, loader
	
	#import sys
	#print sys.exc_info()
	
	t = loader.get_template('pages/500.djt')
	context = { 'MEDIA_URL': settings.MEDIA_URL }
	return HttpResponseServerError(t.render(Context(context)))

def api(request, url):
	'''
	API for detecting format without dirtying the urls file
	'''
	try:
		view, args, kwargs = resolve('/' + url)
	except Resolver404:
		view, args, kwargs = resolve('/' + url + '/')
	kwargs['request'] = request
	return view(*args, **kwargs)

def pages(request, page=None):
	'''
	static pages with API placeholders
	'''
	from django.template.loader import get_template
	template = "pages/%s.djt" % page
	try:
		t = get_template(template)
	except TemplateDoesNotExist:
		raise Http404()
	
	if request.is_json():
		response = HttpResponse(json.dumps('Not this page silly!'))
		response['Content-type'] = 'application/json'
		return response
	
	if request.is_txt():
		response = HttpResponse('Not this page silly!')
		response['Content-type'] = 'text/plain; charset=utf-8'
		return response
	
	return render(request, template, { 'page' : page })


def organizations(request):
	context = {'organizations': get_orgs() }
	orgs = get_orgs()['results']
	half = len(orgs) / 2
	error = None
	if not orgs:
		error = "Issue with phonebook search service"
	context = {
		'error'    : error,
		'orgs_one' : orgs[0:half],
		'orgs_two' : orgs[half:]
	}
	return render(request, "pages/organizations.djt", context)

def organization(request, id):
	from django.template.loader import get_template
	from django.template import Context
	org = get_org(id)
	if not org:
		raise Http404("Organization ID <code>%s</code> could not be found" % (id))
	building = None
	try:
		from campus.models import Building
		building = Building.objects.get(pk=org['bldg_id'])
	except Building.DoesNotExist:
		pass
	context = {'org': org, 'building':building }
	
	if request.is_json():
		context = {'org': org, 'building':building.json() }
		response = HttpResponse(json.dumps(context))
		response['Content-type'] = 'application/json'
		return response
	
	if request.is_ajax():
		if settings.DEBUG:
			import time
			time.sleep(1)
		return render(request, "api/organization.djt", context)
	
	return render(request, "pages/organization.djt", context)

def organization_search(q):
	params = {	'use':'tableSearch', 
				'in':'organizations',
				'search':q}
	url = '?'.join([settings.ORGANIZATION_SEARCH_URL, urllib.urlencode(params)])
	try:
		results = urllib.urlopen(url).read()
		return json.loads(results)
	except:
		logger.error('Issue with organization search service')
		return None

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


def group_search(q):
	from campus.models import Group
	groups = Group.objects.filter(name__icontains=q)
	return groups

def search(request):
	'''
	one day will search over all data available
	'''
	from campus.models import MapObj
	
	found_entries = {'locations':[],'phonebook':[],'organizations':[]}
	query_string  = request.GET.get('q', '').strip()
	
	if bool(query_string):
		
		cache_key  = settings.SEARCH_QUERY_CACHE_PREFIX + hashlib.md5(query_string).hexdigest()
		cache_data = cache.get(cache_key)
		
		if cache_data is not None:
			found_entries = cache_data
		else:
			orgs, locs, phones = ([],[],[])
			
			# Organization Search
			org_response = organization_search(query_string)
			if org_response is not None:
				orgs = org_response['results']
		
			# populate locations by name, abbreviation, and orgs
			q1 = get_query(query_string, ['name',])
			q2 = get_query(query_string, ['abbreviation',])
			q3 = Q(pk = "~~~ no results ~~~")
			for org in orgs:
				q3 = q3 | Q(pk = org['bldg_id'])
			results = MapObj.objects.filter(q1|q2|q3)
			locs = list(results)
		
			# Phonebook Search
			phones_response = phonebook_search(query_string)
			if phones_response is not None:
				phones = phones_response['results']
			
			found_entries = {
				'locations'     : locs,
				'phonebook'     : phones,
				'organizations' : orgs,
			}
			cache.set(cache_key, found_entries, 60 * 60 * 24 * 7)
	
	# TODO: Text API format
	if request.is_json():
		def clean(item): 
			return {
				'type':item.__class__.__name__,
				'name':item.name,
				'id':item.pk,
				'link':item.link}
				
		found_entries['locations'] = map(clean, found_entries['locations'])
		
		search = {
			'query'            : query_string,
			'results'          : found_entries,
			'results_page_url' : '%s?q=%s' % (reverse('search'), query_string)
		}
		response = HttpResponse(json.dumps(search))
		response['Content-type'] = 'application/json'
		return response
	
	else:
		# Do some sorting here to ease the pain in the template
		_locations = []
		
		for loc in found_entries['locations']:
			query_match = loc.name.lower().find(query_string.lower())
			for org in found_entries['organizations']:
				if org['bldg_id'] == loc.pk and query_match != -1:
					_locations.append(loc)
					break

		for loc in found_entries['locations']:
			for org in found_entries['organizations']:
				if org['bldg_id'] == loc.pk and loc not in _locations:
					_locations.append(loc)
					break
		
		for loc in found_entries['locations']:
			if loc not in _locations:
				_locations.append(loc)
		
		found_entries['locations'] = _locations
		
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