# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-08-19 10:51


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campus', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='locations',
            field=models.ManyToManyField(to='campus.GroupedLocation'),
        ),
    ]
