from django.db import models

class Building(models.Model):
	number            = models.CharField("Building Number", max_length=50, primary_key=True)
	name              = models.CharField(max_length=255)
	description       = models.CharField(max_length=255, blank=True)
	image             = models.CharField(max_length=50, blank=True)
	abbreviation      = models.CharField(max_length=50, blank=True)
	poly_coords       = models.TextField(blank=True, null=True)
	illustrated_point = models.CharField(max_length=255, null=True, blank=True)
	googlemap_point   = models.CharField(max_length=255, null=True, blank=True)
	
	
	def _title(self):
		if self.abbreviation:
			return "%s (%s)" % (self.name, self.abbreviation)
		else:
			return self.name
	title = property(_title)
	
	def _link(self):
		from django.core.urlresolvers import reverse
		from django.template.defaultfilters import slugify
		url = reverse('location', kwargs={'loc':self.number})
		return '<a href="%s%s/" data-pk="%s">%s</a>' % (
					url, slugify(self.title), self.number, self.title)
	link = property(_link)
	
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
					obj[f[0]] = json.loads("[{0}]".format(obj[f[0]]))
				continue
			
			# super dumb:
			# http://code.djangoproject.com/ticket/3324
			if not hasattr(f[1], '__type__') or f[1].__type__ != "unicode":
				obj[f[0]] = f[1].__str__()
		return obj
	
	def clean(self, *args, **kwargs):
		from django.core.exceptions import ValidationError
		import json
		
		# change all numbers to be lowercase
		self.number = self.number.lower()
		
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
				json.loads("[{0}]".format(self.illustrated_point))
			except ValueError:
				raise ValidationError("Invalid Illustrated Map Point (not json serializable)")
			
		# check google map point
		if self.googlemap_point != None: 
			try:
				json.loads("[{0}]".format(self.googlemap_point))
			except ValueError:
				raise ValidationError("Invalid Google Map Point (not json serializable)")
		
		super(Building, self).clean(*args, **kwargs)
	
	def __unicode__(self):
		return u'%s' % (self.name)
		
	class Meta:
		ordering = ("name",)

