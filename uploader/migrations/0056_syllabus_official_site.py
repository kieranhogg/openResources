# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0055_auto_20150225_0445'),
    ]

    operations = [
        migrations.AddField(
            model_name='syllabus',
            name='official_site',
            field=models.CharField(max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
    ]
