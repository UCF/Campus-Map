# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'MapObj.address'
        db.add_column(u'campus_mapobj', 'address',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'MapObj.address'
        db.delete_column(u'campus_mapobj', 'address')


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
        u'campus.electricchargingstation': {
            'Meta': {'ordering': "('name',)", 'object_name': 'ElectricChargingStation', '_ormbases': [u'campus.MapObj']},
            u'mapobj_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['campus.MapObj']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'campus.emergencyaed': {
            'Meta': {'ordering': "('name',)", 'object_name': 'EmergencyAED', '_ormbases': [u'campus.MapObj']},
            u'mapobj_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['campus.MapObj']", 'unique': 'True', 'primary_key': 'True'})
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
            'address': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
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
        u'campus.simplesetting': {
            'Meta': {'object_name': 'SimpleSetting'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'value': ('tinymce.models.HTMLField', [], {'null': 'True'})
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
