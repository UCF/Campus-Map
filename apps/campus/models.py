import datetime
import json
import logging
from collections import OrderedDict
from xml.etree.ElementTree import Element

from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.exceptions import FieldError
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.db.models.signals import m2m_changed, post_save
from django.template.defaultfilters import slugify
from django.template.defaultfilters import pluralize
import requests
from tinymce import models as tinymce_models

import campus


log = logging.getLogger(__name__)


class MapQuerySet(QuerySet):
    '''
    Model inheritance with content type and inheritance-aware manager
    thanks: http://djangosnippets.org/snippets/1034/
    '''
    campus_models = False

    def __getitem__(self, k):
        ''' making my querysets act a bit heterogenous'''
        result = super(MapQuerySet, self).__getitem__(k)
        if isinstance(result, models.Model):
            return result.as_leaf_class()
        else:
            return result

    def __iter__(self):
        for item in super(MapQuerySet, self).__iter__():
            yield item.as_leaf_class()

    def get(self, *args, **kwargs):
        # same as getitem, idk why getitem isn't called when this is used
        result = QuerySet.get(self, *args, **kwargs)
        if isinstance(result, models.Model):
            return result.as_leaf_class()
        else:
            return result

    def filter(self, *args, **kwargs):
        '''
        allows to query over all MapObj's, incliding child specfic fields.
        The queryset returned has only MapObj's in it, yet when each one is
        pulled, __getitem__ converts back to original object, creating a
        pseudo heterogenous queryset
        ex:
            can now do
                MapObj.objects.filter(abbreviation="MAP")
                MapObj.objects.filter(permit_type="Greek Row")
            yet these attributes are not apart of MapObj
        '''

        # process the query
        if len(args):
            query = args[0]
        else:
            query = Q(**kwargs)
        new_query = Q(pk="~~~ no results ~~~")
        if query.connector != "OR":
            new_query = query
        else:
            for c in query.children:
                # shoudl probably have some recurrsion here
                # will fail with complex / nested queries
                new_query = new_query | self.leaf_filter(Q(c))

        # return a QuerySet of MapObj's
        return QuerySet.filter(self, new_query)

    def leaf_filter(self, query):
        '''
        Should not be called directly, use filter()
        Executes a query over leaf instances of MapObj
        allows for some complex / cross model queries
        ex:
            q1 = Q(name__icontains='commons')
            q2 = Q(abbreviation__icontains='map')
            MapObj.objects.filter(q1|q2)
        returns:
            [<Group: Ferrell Commons>, <Building: Libra Commons>, <Building: Math & Physics>, ...]
        '''
        # grab all the models that extend MapObj
        if not MapQuerySet.campus_models:
            MapQuerySet.campus_models = []
            for ct in ContentType.objects.filter(app_label="campus"):
                model = models.get_model("campus", ct.model)
                if issubclass(model, campus.models.MapObj):
                    MapQuerySet.campus_models.append(model)

        # return queryset containing MapObj's
        mob_query = Q(pk="~~~ no results ~~~")
        for m in self.campus_models:
            if m == campus.models.MapObj: continue
            try:
                qs = QuerySet(m)
                results = qs.filter(query)
                for o in results:
                    mob_query = mob_query | Q(id=o.mapobj_ptr_id)
            except FieldError:
                continue
        return mob_query


class MapManager(models.Manager):
    def get_query_set(self):
        return MapQuerySet(self.model)

    def mob_filter(self, *args, **kwargs):
        '''
        Needed because plain 'filter' returns leaf class
        '''
        qs = QuerySet(campus.models.MapObj)
        return qs.filter(*args, **kwargs)


class MapObj(models.Model):
    objects = MapManager()
    content_type = models.ForeignKey(ContentType, editable=False, null=True)
    id = models.CharField(max_length=80, primary_key=True, help_text='<strong class="caution">Caution</strong>: changing may break external resources (used for links and images)')
    name = models.CharField(max_length=255, null=True)
    image = models.ImageField(upload_to='uploads/images')
    description = models.CharField(max_length=255, null=True)
    profile = tinymce_models.HTMLField(null=True)
    googlemap_point = models.CharField(max_length=255, null=True, help_text='E.g., <code>[28.6017, -81.2005]</code>')
    illustrated_point = models.CharField(max_length=255, null=True)
    poly_coords = models.TextField(null=True)
    modified = models.DateTimeField(default=datetime.datetime.now)

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            if v in ('', "None", "none", "null"):
                kwargs[k] = None # makes the API a bit uniform
        if kwargs.get('id', False) and not isinstance(kwargs['id'], int):
            kwargs['id'] = kwargs['id'].lower()
        super(MapObj, self).__init__(*args, **kwargs)

    def _title(self):
        if (self.name):
            return self.name
        else:
            return self.id
    title = property(_title)

    def _orgs(self):
        ''' retruns a subset of orgs '''
        from apps.views import get_orgs
        building_orgs = []
        count = 0
        overflow = False
        orgs = get_orgs()
        if orgs:
            for o in orgs['results']:
                if self.pk == str(o['bldg_id']):
                    building_orgs.append(o)
        return {
            "results": building_orgs,
            "overflow": overflow
        }
    orgs = property(_orgs)

    def _object_type(self):
        return self.__class__.__name__
    object_type = property(_object_type)

    def json(self, base_url=''):
        """Returns a json serializable object for this instance"""
        obj = dict(self.__dict__)

        for key, val in obj.items():

            if key == "_state":
                # prevents object.save() function from being destroyed
                # not sure how or why it does, but if object.json() is called
                # first, object.save() will fail
                obj.pop("_state")
                continue

            # with the validator, hopefully this never causes an issue
            if key == "poly_coords":
                if obj["poly_coords"] != None and obj['poly_coords'] != '':
                    obj["poly_coords"] = json.loads(str(obj["poly_coords"]))
                continue
            if key == "illustrated_point" or key == "googlemap_point":
                if obj[key] != None and obj[key] != '':
                    obj[key] = json.loads(str(obj[key]))
                continue

            if isinstance(val, unicode) or isinstance(val, bool) or val==None:
                continue

            # super dumb, concerning floats http://code.djangoproject.com/ticket/3324
            # general catch-all for stuff that makes json cry like like jared's baby
            obj[key] = val.__str__()

        obj['profile_link'] = self._profile_link(base_url)
        obj.pop('content_type_id', None)
        obj.pop('mapobj_ptr_id', None)
        obj['object_type'] = self.object_type
        return obj

    def _kml_coords(self):
        if self.poly_coords == None:
            return None

        def flat(l):
            # recursive function to flatten array and create a a list of coordinates separated by a space
            str = ""
            for i in l:
                if type(i[0]) == type([]):
                    str += flat(i)
                else:
                    str += ("%.6f,%.6f ") % (i[0], i[1])
            return str
        arr = json.loads(self.poly_coords)
        return flat(arr)
    kml_coords = property(_kml_coords)

    def _link(self):
        url = reverse('location', kwargs={'loc': self.id})

        if self.object_type in settings.REDIRECT_TYPES:
            url = "{0}{1}".format(settings.LOCATION_REDIRECT_BASE, slugify(self.name))

        return '<a href="%s/" data-pk="%s">%s</a>' % (url, self.id, self.title)
    link = property(_link)

    def _profile_link(self, base_url=''):
        url = reverse('location', kwargs={'loc': self.id})

        if self.object_type in settings.REDIRECT_TYPES:
            url = "{0}{1}".format(settings.LOCATION_REDIRECT_BASE, slugify(self.name))
            return url

        slug = slugify(self.title)
        if slug in ("", None, False, "None", "none", "null") or slug == self.id:
            return '%s%s' % (base_url, url)
        return '%s%s%s/' % (base_url, url, slug)
    profile_link = property(_profile_link)

    def bxml(self, *args, **kwargs):
        '''
            Representation of this object in Blackbaord Mobile XML.
            Listing only requires names.
            Search requires name, unique building id, and geocode lat long in
            decimal format. Addtional attributes can also be included for search
        '''
        base_url = kwargs.pop('base_url', '')
        name_only = kwargs.pop('name_only', False)

        location = Element('location') # Root

        # Required Attributes
        name = Element('name')
        loc_code = Element('location_code')
        geocode = Element('geocode')
        lat = Element('lat')
        lon = Element('lon')

        name.text = self.title
        loc_code.text = self.id
        if self.googlemap_point:
            lat.text, lon.text = self.googlemap_point[1:-1].replace(' ','').split(',')

        location.append(name)
        if not name_only:
            location.append(loc_code)
            geocode.append(lat)
            geocode.append(lon)
            location.append(geocode)

            # Optional Attributes
            if self.image is not None:
                image = Element('image_url')
                image.text = base_url + settings.MEDIA_URL + self.image
                location.append(image)

            if self.description is not None:
                desc = Element('description')
                desc.text = self.description
                location.append(desc)

            if len(self.orgs['results']) > 0:
                orgs = Element('organizations')
                for org_data in self.orgs['results']:
                    org = Element('organization')
                    org.text = org_data['name']
                    orgs.append(org)
                location.append(orgs)

        return location

    def save(self, *args, **kwargs):
        if(not self.content_type):
            self.content_type = ContentType.objects.get_for_model(self.__class__)

        super(MapObj, self).save(*args, **kwargs)

        if self.content_type.app_label == 'campus':
            gl = GroupedLocation.objects.filter(content_type__pk=self.content_type.pk, object_pk=self.pk)
            if not gl:
                gl = GroupedLocation(content_type=self.content_type, object_pk=self.pk)
                gl.save()

    def as_leaf_class(self):
        content_type = self.content_type
        model = content_type.model_class()
        if (model == MapObj):
            return self
        return model.objects.get(id=self.id)

    @property
    def js_poly_coords(self):
        '''
            Remove all line breaks from poly coord text so it
            can be evaled by JavaScript
        '''
        return self.poly_coords.replace('\n', '').replace('\r', '')

    def __unicode__(self):
        return u'%s' % (self.name)

    class Meta:
        ordering = ("name",)


class Location(MapObj):
    '''
    I don't like this name.  Maybe "miscellaneous locations" or "greater ucf"
    '''
    pass


class RegionalCampus(MapObj):

    class Meta:
        verbose_name_plural = "UCF Connect Locations"


class Building(MapObj):
    abbreviation = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=255, null=True)
    sketchup = models.CharField(max_length=50, null=True, help_text="E.g., https://3dwarehouse.sketchup.com/model.html?id=<code>54b7f313bf315a3a85622796b26c9e66</code>")

    def _number(self):
        return self.id
    number = property(_number)

    def _title(self):
        if self.abbreviation:
            return "%s (%s)" % (self.name, self.abbreviation)
        else:
            return self.name
    title = property(_title)

    def json(self, **kw):
        obj = MapObj.json(self, **kw)
        obj['number'] = self.number
        obj['link'] = self.link
        obj['title'] = self.title
        obj['orgs'] = self.orgs
        return obj

    class Meta:
        ordering = ("name", "id")

parking_permit_colors = OrderedDict()

parking_permit_colors["D Permits"] = "06a54f" #green
parking_permit_colors["Events Garage"] = "bea149" #metalic
parking_permit_colors["B Permits"] = "ee1c23" #red
parking_permit_colors["C Permits"] = "02aeef" #blue
parking_permit_colors["Housing Permits"] = "f47720" #orange
parking_permit_colors["Towers"] = "bc1b8d" #purple


class ParkingLot(MapObj):
    permit_type = models.CharField(max_length=255, null=True)
    abbreviation = models.CharField(max_length=50, null=True)
    sketchup = models.CharField(max_length=50, null=True, help_text="E.g., https://3dwarehouse.sketchup.com/model.html?id=<code>54b7f313bf315a3a85622796b26c9e66</code>")

    def _number(self):
        return self.id
    number = property(_number)

    def _color_fill(self):
        colors = parking_permit_colors
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

    def _title(self):
        if self.abbreviation:
            return "%s (%s)" % (self.name, self.abbreviation)
        else:
            if self.name:
                return self.name
            else:
                return self.id
    title = property(_title)

    def json(self, **kw):
        obj = MapObj.json(self, **kw)
        obj['number'] = self.number
        obj['link'] = self.link
        obj['title'] = self.title
        return obj


class DisabledParking(MapObj):
    num_spaces = models.IntegerField(null=True)

    def json(self, **kw):
        obj = MapObj.json(self, **kw)
        obj['title'] = self.__unicode__()
        return obj

    def save(self, **kwargs):
        if self.id in ("", None, False, "None", "none", "null"):
            # pseduo auto-incredment of key: "disabled-parking-###"
            dp = DisabledParking.objects.all().order_by('-id')[0]
            dp_num = int(dp.id[-3:])
            dp_num += 1
            dp_pk = "disabledparking-%0.3d" % dp_num
            self.id = dp_pk
        super(DisabledParking, self).save(**kwargs)

    def __unicode__(self):
        if self.num_spaces:
            return u'%s (%s space%s)' % (self.description, self.num_spaces, pluralize(self.num_spaces))
        else:
            str = self.description.strip()
            if str == '':
                return '[no description]'
            return self.description

    class Meta:
        verbose_name_plural = "Handicap Parking"


class Sidewalk(models.Model):
    poly_coords = models.TextField(null=True)

    def _kml_coords(self):
        if self.poly_coords == None:
            return None

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
        # keep blanks out of coordinates
        if self.poly_coords == "": self.poly_coords = None

        # check poloy coordinates
        if self.poly_coords != None:
            try:
                json.loads("{0}".format(self.poly_coords))
            except ValueError:
                raise ValidationError("Invalid polygon coordinates (not json serializable)")

        super(Sidewalk, self).clean(*args, **kwargs)


class BikeRack(MapObj):
    pass

class EmergencyPhone(MapObj):
    pass

class EmergencyAED(MapObj):
    pass

class ElectricChargingStation(MapObj):
    pass


class DiningLocation(MapObj):
    address = models.CharField(max_length=255, null=True)

    # Group definition that all DiningLocation objects should
    # exist in
    GROUP            = {'id':'food','name':'Restaurants & Eateries'}

    # Teledata organizations that contain the DiningLocation information in the
    # search service
    ORGANIZATION_IDS = (509,) # RESTAURANTS & EATERIES

    @classmethod
    def refresh(cls):
        '''
            - Fetch the DiningLocation information from the search service.
            - Create/update corresponding DiningLocation objects.
            - Create/update the DiningLocation group.
        '''
        # Get or create the DiningLocation Group
        try:
            group = Group.objects.get(id=cls.GROUP['id'])
        except Group.DoesNotExist:
            group = Group(**cls.GROUP)
            try:
                group.save()
            except Exception, e:
                log.error('Unable to save group: %s' % str(e))

        dining_loc_ctype = ContentType.objects.get(
                                app_label=DiningLocation._meta.app_label,
                                model=DiningLocation.__name__.lower())

        # Talk to search service to get departments
        for org_id in cls.ORGANIZATION_IDS:
            params = {'org__import_id': org_id}
            try:
                page = requests.get(settings.PHONEBOOK + 'departments/',
                                    params=params,
                                    timeout=settings.REQUEST_TIMEOUT,
                                    verify=False)
            except Exception, e:
                log.error('Unable to open URL %s: %s' % (settings.PHONEBOOK, str(e)))
            else:
                try:
                    depts = page.json()
                    depts['results']
                except Exception, e:
                    log.error('Unable to parse JSON: %s' % str(e))
                except KeyError:
                    log.error('Malformed JSON response. Expecting `results` key.')
                else:
                    for dept in depts['results']:
                        # Check existence
                        try:
                            dining_loc = cls.objects.get(id=dept['id'])
                        except DiningLocation.DoesNotExist:
                            dining_loc = cls(id=dept['id'])

                        # Update name and building details
                        dining_loc.name = dept['name']

                        # Look up associated building to fill in coordinates
                        if dept['bldg_id'] is not None:
                            try:
                                building = Building.objects.get(id=dept['bldg_id'])
                            except Building.DoesNotExist:
                                # Assume the teledata is wrong
                                pass
                            else:
                                dining_loc.googlemap_point = building.googlemap_point
                                dining_loc.illustrated_point = building.illustrated_point
                                dining_loc.poly_coords = building.poly_coords
                        try:
                            dining_loc.save()
                        except Exception, e:
                            log.error('Unable to save dining location: %s' % str(e))

                        grouped_location, created = GroupedLocation.objects.get_or_create(object_pk=dining_loc.pk,content_type=dining_loc_ctype)
                        if created:
                            group.locations.add(grouped_location)


class GroupedLocationManager(models.Manager):
    '''
    Used with the managment commands to import/export.  When the many-to-many
    relationship is being dumped, for example locations within a group,
    each location looks like:
    , it looks like:
    "locations": [
        ["campus.building", "406"],
        ...
        ["campus.building", "410"],
    ]
    '''
    def get_by_natural_key(self, content_type, object_pk):
        app_label, model = content_type.split(".")
        content_type = ContentType.objects.get(app_label=app_label, model=model)
        return self.get(content_type=content_type.pk, object_pk=object_pk)


class GroupedLocation(models.Model):
    objects = GroupedLocationManager()

    object_pk = models.CharField(max_length=255)
    content_type = models.ForeignKey(ContentType)
    content_object = generic.GenericForeignKey('content_type', 'object_pk')

    def __unicode__(self):
        loc = self.content_object
        loc_name = str(loc)
        if not loc_name:
            loc_name = "#{0}".format(loc.pk)
        if hasattr(loc, 'abbreviation') and str(loc.abbreviation):
            loc_name = "{0} ({1})".format(loc_name, loc.abbreviation)
        if hasattr(loc, 'number') and str(loc.number):
            loc_name = "{0} | {1}".format(loc_name, loc.number)
        loc_class = loc.__class__.__name__
        return "{0} | {1}".format(loc_class, loc_name)

    def natural_key(self):
        content_type = ".".join(self.content_type.natural_key())
        return (content_type, self.object_pk)
    natural_key.dependencies = ['contenttypes.contenttype']

    class Meta:
        unique_together = (('object_pk', 'content_type'),)


class Group(MapObj):
    locations = models.ManyToManyField(GroupedLocation, null=True)

    def json(self, **kw):
        obj = super(Group, self).json(**kw)
        locations = {}
        locations['count'] = self.locations.count()
        locations['ids'] = []
        locations['links'] = []
        for l in self.locations.all():
            if l.content_object:
                locations['ids'].append(l.content_object.id)
                locations['links'].append(l.content_object.link)
        obj['locations'] = locations
        return obj

    @classmethod
    def update_coordinates(cls, **kwargs):
        sender = kwargs['instance']
        sender.googlemap_point = sender.midpoint('googlemap_point')
        sender.illustrated_point = sender.midpoint('illustrated_point')
        sender.save()

    def midpoint(self, coordinates_field):
        midpoint_func = lambda a, b: [((a[0] + b[0])/2), ((a[1] + b[1])/2)]

        points = [p.content_object for p in self.locations.all()]
        points = [getattr(p, coordinates_field, None) for p in points]
        points = [json.loads(p) for p in points if p is not None]

        if len(points) < 1:
            return None
        if len(points) < 2:
            return json.dumps(points[0])

        midpoint = reduce(midpoint_func, points)
        midpoint = json.dumps(midpoint)
        return midpoint

    def __unicode__(self):
        return self.name

m2m_changed.connect(Group.update_coordinates, sender=Group.locations.through)


class SimpleSetting(models.Model):
    name = models.CharField(max_length=80)
    value = tinymce_models.HTMLField(null=True)
