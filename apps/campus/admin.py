from models import *
from django.contrib import admin

class BuildingAdmin(admin.ModelAdmin):
	list_display = ('name', 'number', 'abbreviation')
	search_fields = ['name']
	actions = None	  
	#change_form_template = 'admin/campus_location.djt';
	
admin.site.register(Building, BuildingAdmin)