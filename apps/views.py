from django.http      import HttpResponse, Http404
from django.views.generic.simple import direct_to_template as render
from django.template import TemplateDoesNotExist

from django.core.cache import cache
import settings, urllib, json

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
		response['Content-type'] = 'text/plain'
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
	return render(request, "pages/organization.djt", {'org': org })


def get_orgs():
	orgs = cache.get('organizations')
	if orgs is None:
		url = settings.PHONEBOOK + '?use=tableSearch&in=organizations&order_by=name&order=ASC'
		results = urllib.urlopen(url).read()
		orgs = json.loads(results)
		cache.set('organizations', orgs)
	return orgs

def get_depts():
	depts = cache.get('departments')
	if depts is None:
		url = settings.PHONEBOOK + '?use=tableSearch&in=departments&order_by=name&order=ASC'
		results = urllib.urlopen(url).read()
		depts = json.loads(results)
		cache.set('departments', depts)
	return depts

def get_org(id):
	orgs = get_orgs()
	for o in orgs['results']:
		if o['id'] == id:
			print o
			print
			depts = get_depts()
			o['departments'] = []
			for d in depts['results']:
				if d['org_id'] == id and d['name'] is not None:
					o['departments'].append(d)
			return o