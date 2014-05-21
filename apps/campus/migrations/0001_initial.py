# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MapObj'
        db.create_table(u'campus_mapobj', (
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True)),
            ('id', self.gf('django.db.models.fields.CharField')(max_length=80, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('profile', self.gf('tinymce.models.HTMLField')(null=True)),
            ('googlemap_point', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('illustrated_point', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('poly_coords', self.gf('django.db.models.fields.TextField')(null=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal(u'campus', ['MapObj'])

        # Adding model 'Location'
        db.create_table(u'campus_location', (
            (u'mapobj_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['campus.MapObj'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'campus', ['Location'])

        # Adding model 'RegionalCampus'
        db.create_table(u'campus_regionalcampus', (
            (u'mapobj_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['campus.MapObj'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'campus', ['RegionalCampus'])

        # Adding model 'Building'
        db.create_table(u'campus_building', (
            (u'mapobj_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['campus.MapObj'], unique=True, primary_key=True)),
            ('abbreviation', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('sketchup', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
        ))
        db.send_create_signal(u'campus', ['Building'])

        # Adding model 'ParkingLot'
        db.create_table(u'campus_parkinglot', (
            (u'mapobj_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['campus.MapObj'], unique=True, primary_key=True)),
            ('permit_type', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('abbreviation', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('sketchup', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
        ))
        db.send_create_signal(u'campus', ['ParkingLot'])

        # Adding model 'DisabledParking'
        db.create_table(u'campus_disabledparking', (
            (u'mapobj_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['campus.MapObj'], unique=True, primary_key=True)),
            ('num_spaces', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'campus', ['DisabledParking'])

        # Adding model 'Sidewalk'
        db.create_table(u'campus_sidewalk', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('poly_coords', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal(u'campus', ['Sidewalk'])

        # Adding model 'BikeRack'
        db.create_table(u'campus_bikerack', (
            (u'mapobj_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['campus.MapObj'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'campus', ['BikeRack'])

        # Adding model 'EmergencyPhone'
        db.create_table(u'campus_emergencyphone', (
            (u'mapobj_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['campus.MapObj'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'campus', ['EmergencyPhone'])

        # Adding model 'DiningLocation'
        db.create_table(u'campus_dininglocation', (
            (u'mapobj_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['campus.MapObj'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'campus', ['DiningLocation'])

        # Adding model 'GroupedLocation'
        db.create_table(u'campus_groupedlocation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('object_pk', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal(u'campus', ['GroupedLocation'])

        # Adding unique constraint on 'GroupedLocation', fields ['object_pk', 'content_type']
        db.create_unique(u'campus_groupedlocation', ['object_pk', 'content_type_id'])

        # Adding model 'Group'
        db.create_table(u'campus_group', (
            (u'mapobj_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['campus.MapObj'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'campus', ['Group'])

        # Adding M2M table for field locations on 'Group'
        m2m_table_name = db.shorten_name(u'campus_group_locations')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('group', models.ForeignKey(orm[u'campus.group'], null=False)),
            ('groupedlocation', models.ForeignKey(orm[u'campus.groupedlocation'], null=False))
        ))
        db.create_unique(m2m_table_name, ['group_id', 'groupedlocation_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'GroupedLocation', fields ['object_pk', 'content_type']
        db.delete_unique(u'campus_groupedlocation', ['object_pk', 'content_type_id'])

        # Deleting model 'MapObj'
        db.delete_table(u'campus_mapobj')

        # Deleting model 'Location'
        db.delete_table(u'campus_location')

        # Deleting model 'RegionalCampus'
        db.delete_table(u'campus_regionalcampus')

        # Deleting model 'Building'
        db.delete_table(u'campus_building')

        # Deleting model 'ParkingLot'
        db.delete_table(u'campus_parkinglot')

        # Deleting model 'DisabledParking'
        db.delete_table(u'campus_disabledparking')

        # Deleting model 'Sidewalk'
        db.delete_table(u'campus_sidewalk')

        # Deleting model 'BikeRack'
        db.delete_table(u'campus_bikerack')

        # Deleting model 'EmergencyPhone'
        db.delete_table(u'campus_emergencyphone')

        # Deleting model 'DiningLocation'
        db.delete_table(u'campus_dininglocation')

        # Deleting model 'GroupedLocation'
        db.delete_table(u'campus_groupedlocation')

        # Deleting model 'Group'
        db.delete_table(u'campus_group')

        # Removing M2M table for field locations on 'Group'
        db.delete_table(db.shorten_name(u'campus_group_locations'))


    models = {
        u'campus.bikerack': {
            'Meta': {'ordering': "('name',)", 'object_name': 'BikeRack', '_ormbases': [u'campus.MapObj']},
            u'mapobj_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['campus.MapObj']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'campus.building': {
            'Meta': {'ordering': "('name', 'id')", 'object_name': 'Building', '_ormbases': [u'campus.MapObj']},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            u'mapobj_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['campus.MapObj']", 'unique': 'True', 'primary_key': 'True'}),
            'sketchup': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'})
        },
        u'campus.dininglocation': {
            'Meta': {'ordering': "('name',)", 'object_name': 'DiningLocation', '_ormbases': [u'campus.MapObj']},
            u'mapobj_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['campus.MapObj']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'campus.disabledparking': {
            'Meta': {'ordering': "('name',)", 'object_name': 'DisabledParking', '_ormbases': [u'campus.MapObj']},
            u'mapobj_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['campus.MapObj']", 'unique': 'True', 'primary_key': 'True'}),
            'num_spaces': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        u'campus.emergencyphone': {
            'Meta': {'ordering': "('name',)", 'object_name': 'EmergencyPhone', '_ormbases': [u'campus.MapObj']},
            u'mapobj_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['campus.MapObj']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'campus.group': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Group', '_ormbases': [u'campus.MapObj']},
            'locations': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['campus.GroupedLocation']", 'null': 'True', 'symmetrical': 'False'}),
            u'mapobj_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['campus.MapObj']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'campus.groupedlocation': {
            'Meta': {'unique_together': "(('object_pk', 'content_type'),)", 'object_name': 'GroupedLocation'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_pk': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'campus.location': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Location', '_ormbases': [u'campus.MapObj']},
            u'mapobj_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['campus.MapObj']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'campus.mapobj': {
            'Meta': {'ordering': "('name',)", 'object_name': 'MapObj'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'googlemap_point': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '80', 'primary_key': 'True'}),
            'illustrated_point': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'poly_coords': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'profile': ('tinymce.models.HTMLField', [], {'null': 'True'})
        },
        u'campus.parkinglot': {
            'Meta': {'ordering': "('name',)", 'object_name': 'ParkingLot', '_ormbases': [u'campus.MapObj']},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            u'mapobj_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['campus.MapObj']", 'unique': 'True', 'primary_key': 'True'}),
            'permit_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'sketchup': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'})
        },
        u'campus.regionalcampus': {
            'Meta': {'ordering': "('name',)", 'object_name': 'RegionalCampus', '_ormbases': [u'campus.MapObj']},
            u'mapobj_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['campus.MapObj']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'campus.sidewalk': {
            'Meta': {'object_name': 'Sidewalk'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'poly_coords': ('django.db.models.fields.TextField', [], {'null': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['campus']