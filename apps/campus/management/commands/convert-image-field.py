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

	_NEW_UPLOAD_PATH = os.path.join(settings.MEDIA_ROOT, 'uploads')

	_RC_IMAGE_PATH  = os.path.join(settings.MEDIA_ROOT, 'images', 'regional-campuses')
	_OLD_IMAGE_PATH = os.path.join(settings.MEDIA_ROOT, 'images', 'buildings')
	_NEW_IMAGE_PATH = os.path.join(_NEW_UPLOAD_PATH,'images')

	_RELATIVE_IMAGE_PATH = 'uploads/images'

	def handle(self, *args, **options):
		#self.move_images()
		#self.alter_image_column()
		#self.prepend_upload_path()
		self.move_rc_images()
		self.register_rc_images()

	def move_images(self):
		'''
			Move static/images/building to static/uploads/images
		'''
		if not os.path.exists(self._NEW_UPLOAD_PATH):
			os.mkdir(self._NEW_UPLOAD_PATH)
		os.rename(self._OLD_IMAGE_PATH, self._NEW_IMAGE_PATH)

	def alter_image_column(self):
		'''
			Alter the MapObj->image column structure to be  VARCHAR(100) NOT NULL
		'''
		cursor = connection.cursor()
		# To avoid a warning, set all NULL entries to empty string
		cursor.execute('UPDATE campus_mapobj SET image = "" WHERE image IS NULL')
		cursor.execute('ALTER TABLE  campus_mapobj CHANGE  image  image VARCHAR( 100 ) NOT NULL')
		transaction.commit_unless_managed()

	def prepend_upload_path(self):
		'''
			Prepend the new image upload path to each MapObj->image entry
		'''
		cursor = connection.cursor()
		cursor.execute('UPDATE campus_mapobj SET image = CONCAT("%s", "/", image) WHERE image != ""' % self._RELATIVE_IMAGE_PATH)
		transaction.commit_unless_managed()

	def move_rc_images(self):
		'''
			Note the names of the regional campus images and copy them into the uploads
			directory.
		'''
		self.rc_image_filenames = os.listdir(self._RC_IMAGE_PATH)

		for filename in self.rc_image_filenames:
			os.rename(os.path.join(self._RC_IMAGE_PATH, filename), os.path.join(self._NEW_IMAGE_PATH, filename))
	def register_rc_images(self):
		'''
			Assign the copied Regional Campus images to their respective locations
		'''
		cursor = connection.cursor()
		for filename in self.rc_image_filenames:
			name, extension = os.path.splitext(filename)
			cursor.execute('UPDATE campus_mapobj SET image = CONCAT("%s", "/", "%s") WHERE id = "%s"' % (self._RELATIVE_IMAGE_PATH, filename, name))
		transaction.commit_unless_managed()