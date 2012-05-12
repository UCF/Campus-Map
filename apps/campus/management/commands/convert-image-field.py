from django.core.management.base import BaseCommand
from django.db                   import connection, transaction
from django.conf                 import settings
import os

class Command(BaseCommand):
	'''
		Converts MapObj->image from a CharField to an ImageField type.

		Current all of the MapObj images are located in static/buildings/.

		This script will do the following:

		- Move {MEDIA_ROOT}/images/buildings to {MEDIA_ROOT}/uploads/images/
		- Alter the MapObj->image column definition to match that of the ImageField type
		- Prepend the new image upload path to each MapObj->image entry
	'''

	_NEW_UPLOAD_PATH = os.path.join(media_root, 'uploads')

	_OLD_IMAGE_PATH = os.path.join(media_root, 'images', 'buildings')
	_NEW_IMAGE_PATH = os.path.join(media_root, 'uploads','images')

	_RELATIVE_IMAGE_PATH = 'static/uploads/images'

	def handle(self, *args, **options):
		media_root = settings.MEDIA_ROOT

		self.move_images()
		self.alter_image_column()
		self.prepend_upload_path()

	def move_images():
		'''
			Move static/images/building to static/uploads/images
		'''
		if not os.path.exists(self._NEW_UPLOAD_PATH):
			os.mkdir(self._NEW_UPLOAD_PATH)
		os.rename(self._OLD_IMAGE_PATH, self._NEW_IMAGE_PATH)

	def alter_image_column():
		'''
			Alter the MapObj->image column structure to be  VARCHAR(100) NOT NULL
		'''
		cursor = connection.cursor()
		cursor.execute('ALTER TABLE  campus_mapobj CHANGE  image  image VARCHAR( 100 ) NOT NULL')
		transaction.commit_unless_managed()

	def prepend_upload_path():
		'''
			Prepend the new image upload path to each MapObj->image entry
		'''
		cursor = connection.cursor()
		cursor.execute('UPDATE campus_mapobj SET image = CONCAT("%s", "/", image) WHERE image != ""' % self._RELATIVE_IMAGE_PATH)
		cursor.commit_unless_managed()