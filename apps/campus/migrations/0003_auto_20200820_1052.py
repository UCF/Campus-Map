# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-08-20 10:52
from __future__ import unicode_literals

from django.db import migrations, models


def abbr_forwards(apps, schema_editor):
    MapObj = apps.get_model('campus', 'MapObj')
    Building = apps.get_model('campus', 'Building')
    ParkingLot = apps.get_model('campus', 'ParkingLot')
    db_alias = schema_editor.connection.alias

    for bldg in Building.objects.using(db_alias).all():
        abbr = bldg.abbreviation # TODO returns None because field doesn't exist on the model anymore? grab via sql instead?
        bldg.__class__ = MapObj
        bldg.abbreviation_migrated = abbr
        bldg.save()
    for plot in ParkingLot.objects.using(db_alias).all():
        abbr = plot.abbreviation # TODO returns None because field doesn't exist on the model anymore? grab via sql instead?
        plot.__class__ = MapObj
        plot.abbreviation_migrated = abbr
        plot.save()

def abbr_backwards(apps, schema_editor):
    # TODO
    return


class Migration(migrations.Migration):

    dependencies = [
        ('campus', '0002_auto_20200819_1051'),
    ]

    operations = [
        migrations.AddField(
            model_name='mapobj',
            name='abbreviation_migrated',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.RunPython(abbr_forwards, abbr_backwards),
        migrations.RemoveField(
            model_name='building',
            name='abbreviation',
        ),
        migrations.RemoveField(
            model_name='parkinglot',
            name='abbreviation',
        ),
        migrations.RenameField(
            model_name='mapobj',
            old_name='abbreviation_migrated',
            new_name='abbreviation'
        )
    ]
