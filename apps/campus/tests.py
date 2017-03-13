"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.conf import settings
from django.core.management import call_command
from django.core.urlresolvers import resolve
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from campus import models

class TestViews(TestCase):

    def init(self):
        """
        Remove logging
        """
        setting.LOGGING = {}

    def _pre_setup(self):
        """
        Setup the fixtures with custom data loader
        """
        super(TestViews, self)._pre_setup()
        call_command('campusdata', test=True, verbosity=0, interactive=False)


    def setUp(self):
        """
        Setup database
        """
        self.client = Client()

    def test_home(self):
        """
        Test home page
        """
        response = self.client.get('/')
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed('campus/base.djt')
        self.assertEquals('null', response.context['infobox_location_id'])
        self.assertIsNone(response.context['geo_placename'])
        self.assertIsNone(response.context['geo_region'])
        self.assertIsNone(response.context['geo_latlng'])
        self.assertIsNotNone(response.context['points'])
        self.assertIn('.kml', response.context['buildings_kml'])
        self.assertIn('.kml', response.context['sidewalks_kml'])
        self.assertIn('.kml', response.context['parking_kml'])
        self.assertIn('location', response.context['loc_url'])
        self.assertIn('parking/.json', response.context['parking_json'])
        self.assertIn('food/.json', response.context['dining_json'])
        self.assertIn('http', response.context['base_url'])

    def test_map_location(self):
        """
        Test map location (?show=1)
        """
        response = self.client.get('/?show=1')
        self.assertEquals(200, response.status_code)
        self.assertTemplateUsed('campus/base.djt')
        self.assertEquals('"1"', response.context['infobox_location_id'])

    def test_page(self):
        """
        Test the url.py page functionality
        """
        response = self.client.get('/printable/')
        self.assertEquals(200, response.status_code)
        self.assertTemplateUsed('pages/printable.djt')

    def test_organizations(self):
        """
        Test organizations
        """
        response = self.client.get('/organizations/')
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed('pages/organizations.djt')
        self.assertIn({u'building': u'Millican Hall', u'name': u'ACADEMIC AFFAIRS', u'phone': u'407-823-2302', u'bldg_id': 1, u'org_id': None, u'id': 354, u'dept_id': None, u'from_table': u'organizations', u'department': None, u'organization': None, u'email': None, u'room': u'338'},
                      response.context['orgs_one'])
        self.assertIn({u'building': u'Knights Plaza', u'name': u'KNIGHTS PLAZA', u'phone': u'407-882-8600', u'bldg_id': 137, u'org_id': None, u'id': 527, u'dept_id': None, u'from_table': u'organizations', u'department': None, u'organization': None, u'email': None, u'room': None},
                      response.context['orgs_two'])

    def test_organization(self):
        """
        Test organization
        """
        response = self.client.get('/locations/1/millican-hall/?org=354')
        self.assertEquals(200, response.status_code)
        self.assertTemplateUsed('pages/location.djt')
        self.assertEquals(u'Millican Hall', response.context['location'].name)
        self.assertEquals(u'Millican Hall', response.context['org'][u'building'])
        self.assertIn({u'building': u'Millican Hall', u'name': u'Academic Affairs', u'phone': u'407-823-4376', u'bldg_id': 1, u'org_id': 354, u'id': 1451, u'dept_id': None, u'from_table': u'departments', u'department': None, u'organization': u'ACADEMIC AFFAIRS', u'email': None, u'room': u'338'},
                      response.context['org']['departments'])
        self.assertEquals('US-FL', response.context['geo_region'])
        self.assertEquals('Orlando', response.context['geo_placename'])
        self.assertEquals(u'[28.598854185535444, -81.202466958930960]', response.context['location'].googlemap_point)

