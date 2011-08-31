'''
	This file is used only for testing code
	
'''
from django.core.management.base import BaseCommand
import os, campus, json
from apps.campus.models import Building, ParkingLot
from django.core.management import call_command

class Command(BaseCommand):
	def handle(self, *args, **options):
		
		STARTS_WITH_FILTER = 'Parking Garage'
		
		for building in Building.objects.filter(name__startswith = STARTS_WITH_FILTER):
			print building.name
			try:
				parking_lot = ParkingLot.objects.get(name = building.name)
			except ParkingLot.DoesNotExist:
				print '>> No matching parking lot found'
			else:
				# Copy sketchup and abbreviation to parking lot and delete the building
				building_dict = building.__dict__
				building.delete()
				
				del building_dict['_state']
				del building_dict['_mapobj_ptr_cache']
				
				building_dict['permit_type'] = parking_lot.permit_type
				building_dict['number'] = parking_lot.number
				building_dict['content_type_id'] = 4
				
				# Reverse the poly coordinates
				#new_poly_coords = []
				#for coord in building_dict['poly_coords']:
				#	new_poly_coords.append(coord[1], coord[0])
				#building_dict['poly_coords'] = new_poly_coords
				
				parking_lot.delete()
				
				new_lot = ParkingLot(**building_dict)
				
				
				
				new_lot.save()