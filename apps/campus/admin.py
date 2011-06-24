from models import *
from django.contrib import admin
import campus
import inspect

class BuildingAdmin(admin.ModelAdmin):
	list_display = ('name', 'number', 'abbreviation')
	search_fields = ['name', 'number', 'abbreviation']
	prepopulated_fields = {'image':('name',)}
	fields = ('name', 'number', 'abbreviation', 'image', 'description', 'profile', 'googlemap_point', 'illustrated_point', 'poly_coords')
	actions = None
	change_form_template = 'admin/maps_point_selector.djt';
admin.site.register(Building, BuildingAdmin)


class RegionalAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug')
	prepopulated_fields = {'slug': ('name',)}
	fields = ('name', 'slug', 'description', 'profile', 'googlemap_point')
	actions = None
	change_form_template = 'admin/maps_point_selector.djt';
admin.site.register(RegionalCampus, RegionalAdmin)

class LocationAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug')
	prepopulated_fields = {'slug': ('name',)}
	fields = ('name', 'slug', 'description', 'googlemap_point')
	actions = None
	change_form_template = 'admin/maps_point_selector.djt';
admin.site.register(Location, LocationAdmin)




class GroupAdmin(admin.ModelAdmin):
	search_fields = ('name',)
	ordering = ('name',)
	filter_horizontal = ('locations',)
	def get_form(self, request, obj=None, **kwargs):
		
		''' ensure all campus locations are groupable '''
		for key in dir(campus.models):
			attr = getattr(campus.models, key)
			if (not inspect.isclass(attr)
				or not issubclass(attr, campus.models.CommonLocation) 
				or attr._meta.abstract ):
				continue
			
			# the attribute is a model we'd like to use for grouping 
			model = attr
			for loc in model.objects.all():
				loc_type = ContentType.objects.get_for_model(loc)
				gl = GroupedLocation.objects.filter(content_type__pk=loc_type.pk, object_pk=loc.pk)
				if not gl:
					gl = GroupedLocation(content_type=loc_type, object_pk=loc.pk)
					gl.save()
		
		''' clean up any deleted locations '''
		for gl in GroupedLocation.objects.all():
			if not gl.content_object:
				gl.delete()
		
		return admin.ModelAdmin.get_form(self, request, obj, **kwargs)

admin.site.register(Group, GroupAdmin)