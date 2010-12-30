from django.db import models

class Building(models.Model):
	number            = models.CharField("Building Number", max_length=50, primary_key=True)
	name              = models.CharField(max_length=255)
	description       = models.CharField(max_length=255, blank=True)
	image             = models.CharField(max_length=50, blank=True)
	abbreviation      = models.CharField(max_length=50, blank=True)
	poly_coords       = models.TextField(blank=True)
	illustrated_point = models.CharField(max_length=255, blank=True)
	googlemap_point   = models.CharField(max_length=255, blank=True)
	
	def json(self):
		"""Returns a json serializable object for this instance"""
		obj = self.__dict__
		# super dumb:
		# http://code.djangoproject.com/ticket/3324
		for f in obj.items():
			if f[0] == "_state":
				# prevents object.save() function from being destroyed
				# not sure how or why it does, but if object.json() is called
				# first, object.save() will fail
				obj.pop("_state")
				continue
			if not hasattr(f[1], '__type__') or f[1].__type__ != "unicode":
				obj[f[0]] = f[1].__str__()
		return obj
		
	def __unicode__(self):
		return u'%s' % (self.name)
		
	class Meta:
		ordering = ("name",)

