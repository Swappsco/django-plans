# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import os
from sys import path
from django.core import serializers

fixture_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../fixtures'))
fixture_filename = 'initial_data.json'

def load_mock_data(apps, schema_editor):
    """
    Fixtures will be removed on django 1.9.
    Using data migrations instead as suggested
    in the documentation.
    """
    fixture_file = os.path.join(fixture_dir, fixture_filename)
    with open(fixture_file, 'rb') as fixture:
        objects = serializers.deserialize('json', fixture, ignorenonexistent=True)
        for obj in objects:
            obj.save()


class Migration(migrations.Migration):

    dependencies = [
        # Requires plans because that will be populated too
        ('foo', '0001_initial'),
        ('plans', '0002_auto_20151111_1101'),
    ]

    operations = [
        migrations.RunPython(load_mock_data),
    ]
