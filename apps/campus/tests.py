"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.conf import settings
from django.core.management import call_command
from django.urls import resolve
from django.urls import reverse
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
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('campus/base.djt')
        self.assertEqual('null', response.context['infobox_location_id'])
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
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed('campus/base.djt')
        self.assertEqual('"1"', response.context['infobox_location_id'])

    def test_page(self):
        """
        Test the url.py page functionality
        """
        response = self.client.get('/printable/')
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed('pages/printable.djt')

    def test_organizations(self):
        """
        Test organizations
        """
        response = self.client.get('/organizations/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('pages/organizations.djt')
        self.assertIn({'building': 'Millican Hall', 'name': 'ACADEMIC AFFAIRS', 'phone': '407-823-2302', 'bldg_id': 1, 'org_id': None, 'id': 354, 'dept_id': None, 'from_table': 'organizations', 'department': None, 'organization': None, 'email': None, 'room': '338'},
                      response.context['orgs_one'])
        self.assertIn({'building': 'Knights Plaza', 'name': 'KNIGHTS PLAZA', 'phone': '407-882-8600', 'bldg_id': 137, 'org_id': None, 'id': 527, 'dept_id': None, 'from_table': 'organizations', 'department': None, 'organization': None, 'email': None, 'room': None},
                      response.context['orgs_two'])

    def test_organization(self):
        """
        Test organization
        """
        response = self.client.get('/locations/1/millican-hall/?org=354')
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed('pages/location.djt')
        self.assertEqual('Millican Hall', response.context['location'].name)
        self.assertEqual('Millican Hall', response.context['org']['building'])
        self.assertIn({'building': 'Millican Hall', 'name': 'Academic Affairs', 'phone': '407-823-4376', 'bldg_id': 1, 'org_id': 354, 'id': 1451, 'dept_id': None, 'from_table': 'departments', 'department': None, 'organization': 'ACADEMIC AFFAIRS', 'email': None, 'room': '338'},
                      response.context['org']['departments'])
        self.assertEqual('US-FL', response.context['geo_region'])
        self.assertEqual('Orlando', response.context['geo_placename'])
        self.assertEqual('[28.598854185535444, -81.202466958930960]', response.context['location'].googlemap_point)

