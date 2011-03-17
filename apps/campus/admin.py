from models import *
from django.contrib import admin

class BuildingAdmin(admin.ModelAdmin):
	list_display = ('name', 'number', 'abbreviation')
	search_fields = ['name', 'number', 'abbreviation']
	prepopulated_fields = {'image':('name',)}
	fields = ('name', 'number', 'abbreviation', 'image', 'description', 'profile', 'googlemap_point', 'illustrated_point', 'poly_coords')
	actions = None
	#change_form_template = 'admin/campus_location.djt';
	
admin.site.register(Building, BuildingAdmin)


class RegionalAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug')
	prepopulated_fields = {'slug': ('name',)}
	fields = ('name', 'slug', 'description', 'profile', 'googlemap_point')
	actions = None
admin.site.register(RegionalCampus, RegionalAdmin)

class LocationAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug')
	prepopulated_fields = {'slug': ('name',)}
	fields = ('name', 'slug', 'description', 'googlemap_point')
	actions = None	  
admin.site.register(Location, LocationAdmin)