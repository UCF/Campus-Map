from django.db import models
from tinymce import models as tinymce_models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

class CommonLocation(models.Model):
	name              = models.CharField(max_length=255)
	image             = models.CharField(max_length=50,  blank=True, help_text='Don&rsquo;t forget to append a file extension')
	description       = models.CharField(max_length=255, blank=True)
	profile           = tinymce_models.HTMLField(blank=True, null=True)
	googlemap_point   = models.CharField(max_length=255, null=True, blank=True, help_text='E.g., <code>[28.6017, -81.2005]</code>')
	illustrated_point = models.CharField(max_length=255, null=True, blank=True)
	poly_coords       = models.TextField(blank=True, null=True)
	
	def json(self):
		"""Returns a json serializable object for this instance"""
		import json
		obj = self.__dict__
		
		for f in obj.items():
			
			if f[0] == "_state":
				# prevents object.save() function from being destroyed
				# not sure how or why it does, but if object.json() is called
				# first, object.save() will fail
				obj.pop("_state")
				continue
			
			# with the validator, hopefully this never causes an issue
			if f[0] == "poly_coords":
				if obj["poly_coords"] != None:
					obj["poly_coords"] = json.loads(str(obj["poly_coords"]))
				continue
			if f[0] == "illustrated_point" or f[0] == "googlemap_point":
				if obj[f[0]] != None:
					obj[f[0]] = json.loads(str(obj[f[0]]))
				continue
			
			if isinstance(f[1], unicode):
				continue
			
			# super dumb, concerning floats http://code.djangoproject.com/ticket/3324
			obj[f[0]] = f[1].__str__()
		
		# add profile link
		if hasattr(self, 'profile_link'):
			obj['profile_link'] = str(self.profile_link)
		
		return obj
	
	def clean(self, *args, **kwargs):
		from django.core.exceptions import ValidationError
		import json
		
		# keep blanks out of coordinates
		if self.poly_coords       == "": self.poly_coords       = None
		if self.illustrated_point == "": self.illustrated_point = None
		if self.googlemap_point   == "": self.googlemap_point   = None
		
		# check poloy coordinates
		if self.poly_coords != None: 
			try:
				json.loads("{0}".format(self.poly_coords))
			except ValueError:
				raise ValidationError("Invalid polygon coordinates (not json serializable)")
		
		# check illustrated point
		if self.illustrated_point != None: 
			try:
				json.loads("{0}".format(self.illustrated_point))
			except ValueError:
				raise ValidationError("Invalid Illustrated Map Point (not json serializable)")
			
		# check google map point
		if self.googlemap_point != None: 
			try:
				json.loads("{0}".format(self.googlemap_point))
			except ValueError:
				raise ValidationError("Invalid Google Map Point (not json serializable)")
		
		super(CommonLocation, self).clean(*args, **kwargs)
	
	def __unicode__(self):
		return u'%s' % (self.name)
		
	class Meta:
		ordering = ("name",)
		abstract = True

class Location(CommonLocation):
	'''
	I don't like this name.  There should never be a specific instance of "Location"
	Throughout this project, the words "location" and "locations" should be abstract over every instance of CommonLocation
	I want to change it to something else, suggestions?
	'''
	slug              = models.SlugField(max_length=255, primary_key=True, help_text='<strong class="caution">Caution</strong>: changing may break external resources (used for links and images)')
	
	class Meta:
		ordering = ("name",)

class RegionalCampus(CommonLocation):
	slug              = models.SlugField(max_length=255, primary_key=True, help_text='<strong class="caution">Caution</strong>: changing may break external resources (used for links and images)')
	
	def _img_tag(self):
		import settings
		image_url = settings.MEDIA_URL + 'images/regional-campuses/' + self.slug + '.jpg'
		return '<img src="%s" alt="%s">' % (image_url, self.description)
	img_tag = property(_img_tag)
	
	class Meta:
		ordering = ("name",)
		verbose_name_plural = "Regional Campuses"

class Building(CommonLocation):
	number            = models.CharField("Building Number", max_length=50, primary_key=True)
	abbreviation      = models.CharField(max_length=50, blank=True)
	
	def _title(self):
		if self.abbreviation:
			return "%s (%s)" % (self.name, self.abbreviation)
		else:
			return self.name
	title = property(_title)
	
	def _link(self):
		url = reverse('location', kwargs={'loc':self.number})
		return '<a href="%s%s/" data-pk="%s">%s</a>' % (url, slugify(self.title), self.number, self.title)
	link = property(_link)
	
	def _profile_link(self):
		url = reverse('location', kwargs={'loc':self.number})
		return '%s%s/' % (url, slugify(self.title))
	profile_link = property(_profile_link)
	
	def clean(self, *args, **kwargs):
		super(Building, self).clean(*args, **kwargs)
		
		# change all numbers to be lowercase
		self.number = self.number.lower()
	
	def _orgs(self, limit=5):
		''' retruns a subset of orgs '''
		from apps.views import get_orgs
		building_orgs = []
		count    = 0
		overflow = False
		for o in get_orgs()['results']:
			if self.pk == o['bldg_id']:
				building_orgs.append(o)
				count += 1
			if(limit > 0 and count >= limit):
				overflow = True
				break
		return {
			"results" : building_orgs,
			"overflow": overflow
		}
	orgs = property(_orgs)
	
	
	class Meta:
		ordering = ("name",)

class ParkingLot(CommonLocation):
	permit_type = models.CharField(max_length=255, blank=True, null=True)
	number      = models.CharField(max_length=50, blank=True, null=True)
	
	def _kml_coords(self):
		if self.poly_coords == None:
			return None
		
		import json
		def flat(l):
			''' 
			recursive function to flatten array and create a a list of coordinates separated by a space
			'''
			str = ""
			for i in l:
				if type(i[0]) == type([]):
					return flat(i)
				else:
					str += ("%.6f,%.6f ")  % (i[0], i[1])
			return str
		
		
		arr = json.loads(self.poly_coords)
		return flat(arr)
	kml_coords = property(_kml_coords)
	
	
	def _color_fill(self):
		
		colors = {
			"B Permits"       : "cc0400", #red
			"C Permits"       : "0052d9", #blue
			"D Permits"       : "009a36", #green
			"Housing Permits" : "ffba00", #orange
			"Greek Row"       : "eb00e3", #pink
		}
		
		rgb = colors.get(self.permit_type) or 'fffb00' #default=yellow
		opacity = .35
		
		# kml is weird, it goes [opacity][blue][green][red] (each two digit hex)
		kml_color = "%x%s%s%s" % (int(opacity*255), rgb[4:], rgb[2:4], rgb[0:2])
		return kml_color
	color_fill = property(_color_fill)
	
	def _color_line(self):
		# same as fill, up opacity
		color = self.color_fill
		opacity = .70
		kml_color = "%x%s" % (opacity * 255, color[2:])
		return kml_color
	color_line = property(_color_line)


class Sidewalk(models.Model):
	poly_coords       = models.TextField(blank=True, null=True)
	
	def _kml_coords(self):
		if self.poly_coords == None:
			return None
		
		import json
		def flat(l):
			''' 
			recursive function to flatten array and create a a list of coordinates separated by a space
			'''
			str = ""
			for i in l:
				if type(i[0]) == type([]):
					return flat(i)
				else:
					str += ("%.6f,%.6f ")  % (i[0], i[1])
			return str
		
		
		arr = json.loads(self.poly_coords)
		return flat(arr)
	kml_coords = property(_kml_coords)
	
	
	def clean(self, *args, **kwargs):
		from django.core.exceptions import ValidationError
		import json
		
		# keep blanks out of coordinates
		if self.poly_coords       == "": self.poly_coords       = None
		
		# check poloy coordinates
		if self.poly_coords != None: 
			try:
				json.loads("{0}".format(self.poly_coords))
			except ValueError:
				raise ValidationError("Invalid polygon coordinates (not json serializable)")
		
		super(Sidewalk, self).clean(*args, **kwargs)

class BikeRack(CommonLocation):
	pass

class EmergencyPhone(CommonLocation):
	pass

class GroupedLocation(models.Model):
	object_pk    = models.CharField(max_length=255)
	content_type = models.ForeignKey(ContentType)
	content_object = generic.GenericForeignKey('content_type', 'object_pk')
	def __unicode__(self):
		loc      = self.content_object
		loc_name = str(loc)
		if not loc_name:
			loc_name = "#{0}".format(loc.pk)
		if hasattr(loc, 'abbreviation') and str(loc.abbreviation):
			loc_name = "{0} ({1})".format(loc_name, loc.abbreviation)
		if hasattr(loc, 'number') and str(loc.number):
			loc_name = "{0} | {1}".format(loc_name, loc.number)
		loc_class = loc.__class__.__name__
		return "{0} | {1}".format(loc_class, loc_name)

class Group(models.Model):
	name = models.CharField(max_length=80, unique=True)
	locations = models.ManyToManyField(GroupedLocation, blank=True)
	def __unicode__(self):
		return self.name
