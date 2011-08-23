from models import *
from django.db import models
from django.contrib import admin
import campus
import inspect

class BuildingAdmin(admin.ModelAdmin):
	list_display = ('name', 'id', 'abbreviation')
	search_fields = ['name', 'id', 'abbreviation']
	prepopulated_fields = {'id':('name',)}
	fields = ('name', 'id', 'abbreviation', 'image', 'description', 'profile', 'sketchup', 'googlemap_point', 'illustrated_point', 'poly_coords')
	actions = None
	change_form_template = 'admin/maps_point_selector.djt';
admin.site.register(Building, BuildingAdmin)


class RegionalAdmin(admin.ModelAdmin):
	list_display = ('name', 'id')
	prepopulated_fields = {'id': ('name',)}
	fields = ('name', 'id', 'description', 'profile', 'googlemap_point')
	actions = None
	change_form_template = 'admin/maps_point_selector.djt';
admin.site.register(RegionalCampus, RegionalAdmin)


class LocationAdmin(admin.ModelAdmin):
	list_display = ('name', 'id')
	prepopulated_fields = {'id': ('name',)}
	fields = ('name', 'id', 'description', 'googlemap_point')
	actions = None
	change_form_template = 'admin/maps_point_selector.djt';
admin.site.register(Location, LocationAdmin)


class HandicappedParkingAdmin(admin.ModelAdmin):
	list_display         = ('name',)
	fields               = ('name', 'googlemap_point',)
	actions              = None
	change_form_template = 'admin/maps_point_selector.djt'
admin.site.register(HandicappedParking, HandicappedParkingAdmin)


def create_groupable_locations():
	''' ensure all campus locations are groupable '''
	for ct in ContentType.objects.filter(app_label="campus"):
		model = models.get_model("campus", ct.model)
		if not issubclass(model, campus.models.MapObj):
			continue
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

class GroupAdmin(admin.ModelAdmin):
	search_fields = ('name',)
	#exclude = ('googlemap_point', 'illustrated_point',)
	prepopulated_fields = {'id' : ('name',)}
	ordering = ('name',)
	fields = ('name', 'id', 'locations', 'image', 'description', 'profile', 'googlemap_point', 'illustrated_point', 'poly_coords')
	filter_horizontal = ('locations',)
	actions = None
	
	def get_form(self, request, obj=None, **kwargs):
		create_groupable_locations()
		return admin.ModelAdmin.get_form(self, request, obj, **kwargs)
admin.site.register(Group, GroupAdmin)