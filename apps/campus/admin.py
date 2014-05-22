import inspect
import sys

from django.db import models
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import CharField
from django.forms import ModelForm
from django.template.defaultfilters import slugify
from tinymce.widgets import AdminTinyMCE

import campus
from models import *


class MapObjForm(ModelForm):
    def __init__(self, *args, **kwargs):
        # extending field options to add "required=False"
        # allows me to create models without "blank=True" everwhere, don't want blanks
        for field,form_field in self.base_fields.items():
            if field in ('name', 'id'):
                continue
            try:
                form_field.required = False
                #form_field.widget.attrs['required'] = "required"
            except AttributeError: pass
        super(MapObjForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        # keep id / building numbers lowercase
        try:
            slugged = slugify(self.cleaned_data['id'])
            if self.cleaned_data['id'] != slugged:
                raise ValidationError("Invalid Location ID (allowed: lowercase alpha, numbers, dashes).  Suggestion: %s" % slugged)
        except KeyError:
            return super(MapObjForm, self).clean(*args, **kwargs)

        # keep blanks out of data (makes the API more uniform)
        for k,v in self.cleaned_data.items():
            try:
                if v.strip() in (None, "", "None", "none", "null"):
                    self.cleaned_data[k] = None
            except AttributeError:
                pass # complex field (like m2m selector)

        # check poly coordinates
        try:
            coords = self.cleaned_data['poly_coords']
            if coords: json.loads(coords)
        except KeyError:
            pass # poly cords not used (like regional campuses)
        except ValueError:
            raise ValidationError("Invalid polygon coordinates (not json serializable)")

        # check illustrated point
        try:
            point = self.cleaned_data['illustrated_point']
            if point: json.loads(point)
        except KeyError:
            pass # poly cords not used (like regional campuses)
        except ValueError:
            raise ValidationError("Invalid Illustrated Map Point (not json serializable)")

        # check google map point
        try:
            point = self.cleaned_data['googlemap_point']
            if point: json.loads(point)
        except KeyError:
            pass # not present in read only (like groups)
        except ValueError:
            raise ValidationError("Invalid Google Map Point (not json serializable)")

        return super(MapObjForm, self).clean(*args, **kwargs)


    class Meta:
        model = campus.models.MapObj


class BuildingForm(MapObjForm):
    class Meta:
        model = campus.models.Building


class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'abbreviation')
    search_fields = ['name', 'id', 'abbreviation']
    prepopulated_fields = {'id':('name',)}
    fields = ('name', 'id', 'abbreviation', 'image', 'description', 'profile', 'sketchup', 'googlemap_point', 'illustrated_point', 'poly_coords')
    actions = None
    change_form_template = 'admin/maps_point_selector.djt'
    form = BuildingForm
admin.site.register(campus.models.Building, BuildingAdmin)



class RegionalAdminForm(MapObjForm):
    class Meta:
        model = campus.models.RegionalCampus


class RegionalAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    prepopulated_fields = {'id': ('name',)}
    fields = ('name', 'id', 'image', 'description', 'profile', 'googlemap_point')
    actions = None
    change_form_template = 'admin/maps_point_selector.djt'
    form = RegionalAdminForm
admin.site.register(campus.models.RegionalCampus, RegionalAdmin)


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    prepopulated_fields = {'id': ('name',)}
    fields = ('name', 'id', 'description', 'googlemap_point')
    actions = None
    change_form_template = 'admin/maps_point_selector.djt';
admin.site.register(campus.models.Location, LocationAdmin)


class DisabledParkingAdminForm(MapObjForm):
    class Meta:
        model = campus.models.DisabledParking


class DisabledParkingAdmin(admin.ModelAdmin):
    fields = ('description', 'num_spaces', 'googlemap_point', 'illustrated_point')
    actions = None
    form = DisabledParkingAdminForm
    change_form_template = 'admin/maps_point_selector.djt'
admin.site.register(campus.models.DisabledParking, DisabledParkingAdmin)


class ParkingLotAdminForm(MapObjForm):
    class Meta:
        model = campus.models.ParkingLot


class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    fields = ('name', 'id', 'image', 'description', 'permit_type', 'abbreviation', 'sketchup', 'googlemap_point', 'illustrated_point', 'poly_coords')
    actions = None
    form = ParkingLotAdminForm
    change_form_template = 'admin/maps_point_selector.djt'
admin.site.register(campus.models.ParkingLot, ParkingLotAdmin)


def create_groupable_locations(**kwargs):
    verbosity = kwargs.get('verbosity', 0)

    ''' ensure all campus locations are groupable '''
    for ct in ContentType.objects.filter(app_label="campus"):
        model = models.get_model("campus", ct.model)

        ''' clean up content type, unused content types are created from going back/forth between map version and renaming models '''
        if model is None:
            ct.delete()
            continue

        if not issubclass(model, campus.models.MapObj):
            continue
        for loc in model.objects.all():
            loc_type = ContentType.objects.get_for_model(loc)
            gl = campus.models.GroupedLocation.objects.filter(content_type__pk=loc_type.pk, object_pk=loc.pk)
            if not gl:
                gl = campus.models.GroupedLocation(content_type=loc_type, object_pk=loc.pk)
                gl.save()
        if verbosity > 0:
            sys.stdout.write(".")
            sys.stdout.flush()

    ''' clean up any deleted locations '''
    for gl in campus.models.GroupedLocation.objects.all():
        if not gl.content_object:
            gl.delete()

class GroupForm(MapObjForm):
    class Meta:
        model = campus.models.Group


class GroupAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    #exclude = ('googlemap_point', 'illustrated_point',)
    prepopulated_fields = {'id' : ('name',)}
    ordering = ('name',)
    fields = ('name', 'id', 'locations', 'image', 'description', 'profile', 'googlemap_point', 'illustrated_point',)
    readonly_fields = ('googlemap_point', 'illustrated_point') # generated by midpoint formula
    filter_horizontal = ('locations',)
    actions = None
    form = GroupForm

    def get_form(self, request, obj=None, **kwargs):
        create_groupable_locations()
        return admin.ModelAdmin.get_form(self, request, obj, **kwargs)
admin.site.register(campus.models.Group, GroupAdmin)


class DiningLocationForm(MapObjForm):
    class Meta:
        model = campus.models.DiningLocation


class DiningLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    prepopulated_fields = {'id': ('name',)}
    fields = ('name', 'id', 'googlemap_point', 'illustrated_point')
    actions = None
    change_form_template = 'admin/maps_point_selector.djt'
    form                 = DiningLocationForm
admin.site.register(campus.models.DiningLocation, DiningLocationAdmin)


class BusCategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'id', )
    fields = ('name', )
admin.site.register(campus.models.BusCategory, BusCategoryAdmin)


class BusRouteAdmin(admin.ModelAdmin):
    search_fields = ('shortname',)
    list_display = ('id', 'shortname', 'category', 'description',)
    fields = ('id', 'shortname', 'category', 'description',)
admin.site.register(campus.models.BusRoute, BusRouteAdmin)


class SimpleSettingAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name',)
    fields = ('name', 'value',)
admin.site.register(campus.models.SimpleSetting, SimpleSettingAdmin)
