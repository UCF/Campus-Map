from django.core.management.base import BaseCommand
from django.conf        import settings
from apps.campus.models import DiningLocation, Building, GroupedLocation, Group
from django.utils       import simplejson
from django.contrib.contenttypes.models import ContentType
import logging
import urllib

log = logging.getLogger(__name__)

ORGANIZATION_IDS = (
			#96, # DINING SERVICES
			509, # RESTAURANTS & EATERIES
		)

GROUP = {'id':'food','name':'Restaurants & Eateries'}

class Command(BaseCommand):
	args = 'none'
	help = 'create dining location objects'

	def handle(self, *args, **options):
		try:
			group = Group.objects.get(id=GROUP['id'])
		except Group.DoesNotExist:
			group = Group(**GROUP)
			try:
				group.save()
			except Exception, e:
				log.error('Unable to save group: %s' % str(e))
		
		dining_loc_ctype = ContentType.objects.get(app_label=DiningLocation._meta.app_label,model=DiningLocation.__name__.lower())
		# Talk to search service to get departments
		for org_id in ORGANIZATION_IDS:
			params = {'in':'departments','search':org_id}
			try:
				url  = '?'.join([settings.PHONEBOOK, urllib.urlencode(params)])
				page = urllib.urlopen(url)
			except Exception, e:
				log.error('Unabe to open URL %s: %s' % (url, str(e)))
			else:
				try:
					depts = simplejson.loads(page.read())
					depts['results']
				except Exception, e:
					log.error('Unable to parse JSON: %s' % str(e))
				except KeyError:
					log.error('Malformed JSON response. Expecting `results` key.')
				else:
					for dept in depts['results']:
						# Check existence
						try:
							dining_loc = DiningLocation.objects.get(id=dept['id'])
						except DiningLocation.DoesNotExist:
							dining_loc = DiningLocation(id=dept['id'])
						
						# Update name and building details
						dining_loc.name = dept['name']

						# Look up associated building to fill in coordinates
						if dept['bldg_id'] is not None:
							try:
								building = Building.objects.get(id=dept['bldg_id'])
							except Building.DoesNotExist:
								pass
							else:
								dining_loc.googlemap_point   = building.googlemap_point
								dining_loc.illustrated_point = building.illustrated_point
								dining_loc.poly_coords       = building.poly_coords
						try:
							dining_loc.save()
						except Exception, e:
							log.error('Unable to save dining location: %s' % str(e))

						created, grouped_location = GroupedLocation.objects.get_or_create(object_pk=dining_loc.pk,content_type=dining_loc_ctype)
						if created:
							group.locations.add(grouped_location)



