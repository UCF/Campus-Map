import os
import shutil
import sys


from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from campus.models import RegionalCampus


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

    _OLD_IMAGE_PATH = os.path.join(settings.PROJECT_FOLDER, 'data', 'images')
    _NEW_IMAGE_PATH = os.path.join(_NEW_UPLOAD_PATH,'images')

    _RELATIVE_IMAGE_PATH = 'uploads/images'

    def handle(self, *args, **options):
        self.move_images()
        self.alter_image_column()
        self.prepend_upload_path()
        self.register_rc_images()

    def move_images(self):
        '''
            Move data/images/ to static/uploads/images
        '''
        sys.stdout.write('Moving static/images/building to static/uploads/images...')
        if not os.path.exists(self._NEW_UPLOAD_PATH):
            os.mkdir(self._NEW_UPLOAD_PATH)
        shutil.copytree(self._OLD_IMAGE_PATH, self._NEW_IMAGE_PATH)
        sys.stdout.write('done\n')

    def alter_image_column(self):
        '''
            Alter the MapObj->image column structure to be  VARCHAR(100) NOT NULL
        '''
        sys.stdout.write('Altering MapObj->image column to VARCHAR(100) NOT NULL...')
        cursor = connection.cursor()
        # To avoid a warning, set all NULL entries to empty string
        cursor.execute('UPDATE campus_mapobj SET image = "" WHERE image IS NULL')
        cursor.execute('ALTER TABLE  campus_mapobj CHANGE  image  image VARCHAR( 100 ) NOT NULL')
        transaction.commit_unless_managed()
        sys.stdout.write('done\n')

    def prepend_upload_path(self):
        '''
            Prepend the new image upload path to each MapObj->image entry
        '''
        sys.stdout.write('Prepending new upload path to MapObj->image column...')
        cursor = connection.cursor()
        cursor.execute('UPDATE campus_mapobj SET image = CONCAT("%s", "/", image) WHERE image != ""' % self._RELATIVE_IMAGE_PATH)
        transaction.commit_unless_managed()
        sys.stdout.write('done\n')

    def register_rc_images(self):
        '''
            Assign the copied UCF Connect location images to their respective locations
        '''
        sys.stdout.write('Assigning UCF Connect location images to MapObj entries...')

        cursor = connection.cursor()
        for campus in RegionalCampus.objects.all():
            cursor.execute('UPDATE campus_mapobj SET image = CONCAT("%s", "/", "%s") WHERE id = "%s"' % (self._RELATIVE_IMAGE_PATH, campus.id + '.jpg', campus.id))
        transaction.commit_unless_managed()
        sys.stdout.write('done\n')
