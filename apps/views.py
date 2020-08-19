from xml.etree import ElementTree
import hashlib
import json
import logging
import re
import sys

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.urlresolvers import Resolver404
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template import Context
from django.template import loader
from django.template import RequestContext
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.html import strip_tags
import requests

from campus.views import home

logger = logging.getLogger(__name__)


def page_not_found(request, **kwargs):
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
        msg = {"error": strip_tags(error)}
        response = HttpResponseNotFound(json.dumps(msg))
        response['Content-type'] = 'application/json'
        return response

    if request.is_txt():
        msg = "404 Not Found:\n%s" % strip_tags(error)
        response = HttpResponseNotFound(msg)
        response['Content-type'] = 'text/plain; charset=utf-8'
        return response

    # must clear query string
    request.GET = {}
    html = home(request, points=True, error=error)
    return HttpResponseNotFound(html)


def server_error(request, **kwargs):
    t = loader.get_template('pages/500.djt')
    context = {'MEDIA_URL': settings.MEDIA_URL}
    return HttpResponseServerError(t.render(Context(context)))


def print_layout(request):
    loc = request.GET.get('show', False)
    error = False
    illustrated = request.GET.has_key('illustrated')
    if loc:
        try:
            from campus.models import MapObj
            loc = MapObj.objects.get(id=loc)
        except MapObj.DoesNotExist:
            loc = False
            error = "Location not found"

    return render(request, 'pages/print.djt', locals())


def pages(request, page=None):
    '''
    static pages with API placeholders
    '''
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

    return render(request, template, {'page': page})


def organizations(request):
    context = {'organizations': get_orgs()}
    orgs = get_orgs()['results']
    half = len(orgs) / 2
    error = None
    if not orgs:
        error = "Issue with phonebook search service"
    context = {
        'error': error,
        'orgs_one': orgs[0:half],
        'orgs_two': orgs[half:]
    }

    return render(request, 'pages/organizations.djt', context)


def organization(request, id):
    org = get_org(id)
    if not org:
        raise Http404("Organization ID <code>%s</code> could not be found" % (id))

    building = None
    try:
        from campus.models import Building
        building = campus.models.Building.objects.get(pk=str(org['bldg']['import_id']))
    except campus.models.Building.DoesNotExist:
        pass
    context = {'org': org, 'building': building}

    if request.is_json():
        context = {'org': org, 'building': building.json()}
        response = HttpResponse(json.dumps(context))
        response['Content-type'] = 'application/json'
        return response

    if request.is_ajax():
        if settings.DEBUG:
            import time
            time.sleep(1)
        template = 'api/organization.djt'
    else:
        template = 'pages/organization.djt'

    return render(request, template, context)


def organization_search(q):
    params = {'use': 'organizations',
              'search': q}
    try:
        results = requests.get(settings.PHONEBOOK,
                               params=params,
                               timeout=settings.REQUEST_TIMEOUT,
                               verify=False).json()
        return results
    except:
        logger.error('Issue with organization search service')
        return None


class Orgs:
    data = None

    @classmethod
    def fetch(cls):
        payload = {'ordering': 'name'}
        try:
            orgs = requests.get(settings.PHONEBOOK + 'organizations/',
                                params=payload,
                                timeout=settings.REQUEST_TIMEOUT,
                                verify=False).json()
            cls.data = orgs
            return True
        except:
            return False


def get_orgs():
    if Orgs.data is None:
        result = Orgs.fetch()
        if not result:
            print "Issue with phonebook search service"
            return None
    return Orgs.data


def get_depts():
    payload = {'ordering': 'name'}
    try:
        depts = requests.get(settings.PHONEBOOK + 'departments/',
                             params=payload,
                             timeout=settings.REQUEST_TIMEOUT,
                             verify=False).json()
    except:
        print "Issue with phonebook search service"
        return None

    return depts


def get_org(id):
    orgs = get_orgs()
    for o in orgs['results']:
        if str(o['import_id']) == id:
            depts = get_depts()
            o['departments'] = []
            for d in depts['results']:
                if str(d['org']['import_id']) == id and d['name'] is not None:
                    o['departments'].append(d)
            return o


def phonebook_search(q):
    try:
        results = requests.get(settings.PHONEBOOK,
                               params={'search': q},
                               timeout=settings.REQUEST_TIMEOUT,
                               verify=False).json()
        return results
    except:
        print "Issue with phonebook search service"
        return None


def group_search(q):
    groups = campus.models.Group.objects.filter(name__icontains=q)
    return groups

def search(request):
    '''
    one day will search over all data available
    '''
    found_entries = {'locations': [], 'phonebook': [], 'organizations': []}
    query_string = request.GET.get('q', '').strip()
    extended = request.GET.get('extended', False) in ['1', 'true', 'True']

    if bool(query_string):
        orgs, locs, phones = ([], [], [])

        # Organization Search
        org_response = organization_search(query_string)
        if org_response is not None:
            orgs = org_response['results']

        # populate locations by name, abbreviation, and orgs
        q1 = get_query(query_string, ['name', ])
        q2 = get_query(query_string, ['abbreviation', ])
        q3 = Q(pk="~~~ no results ~~~")
        for org in orgs:
            q3 = q3 | Q(pk=str(org['bldg_id']))
        from campus.models import MapObj
        results = MapObj.objects.filter(q1 | q2 | q3)
        locs = list(results)

        # Phonebook Search
        phones_response = phonebook_search(query_string)
        if phones_response is not None:
            phones = phones_response['results']

        found_entries = {
            'locations': locs,
            'phonebook': phones,
            'organizations': orgs,
        }

    if request.is_bxml():
        base_url = request.build_absolute_uri(reverse('campus.views.home'))[:-1]
        xml_locations = ElementTree.Element('Locations')
        for location in list(l.bxml(base_url=base_url) for l in found_entries['locations']):
            xml_locations.append(location)
        response = HttpResponse(ElementTree.tostring(xml_locations,
                                                     encoding="UTF-8"))
        response['Content-type'] = 'application/xml'
        return response

    if request.is_json():
        def clean(item):
            return {
                'type': item.__class__.__name__,
                'name': item.name,
                'id': item.pk,
                'link': item.link}

        def extended_meta(item):
            return item.json()

        if extended:
            found_entries['locations'] = map(extended_meta, found_entries['locations'])
        else:
            found_entries['locations'] = map(clean, found_entries['locations'])

        search = {
            'query': query_string,
            'results': found_entries,
            'results_page_url': '%s?q=%s' % (reverse('search'), query_string)
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
                if str(org['bldg']['import_id']) == loc.pk and query_match != -1:
                    _locations.append(loc)
                    break

        for loc in found_entries['locations']:
            for org in found_entries['organizations']:
                if str(org['bldg']['import_id']) == loc.pk and loc not in _locations:
                    _locations.append(loc)
                    break

        for loc in found_entries['locations']:
            if loc not in _locations:
                _locations.append(loc)

        found_entries['locations'] = _locations

        context = {'search': True, 'query': query_string, 'results': found_entries}

        return render(request, 'campus/search.djt', context)


# thanks:  http://www.julienphalip.com/blog/2008/08/16/adding-search-django-site-snap/
def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
    '''
        Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example:

        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
    '''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]


# thanks:  http://www.julienphalip.com/blog/2008/08/16/adding-search-django-site-snap/
def get_query(query_string, search_fields):
    '''
        Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.
    '''

    # Query to search for every search term
    query = None
    terms = normalize_query(query_string)
    for term in terms:
        # Query to search for a given term in each field
        or_query = None
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
