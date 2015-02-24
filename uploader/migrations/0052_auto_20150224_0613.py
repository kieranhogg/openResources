# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0051_auto_20150223_0638'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='examlevel',
            options={'ordering': ('country', 'level_number', 'level_name')},
        ),
        migrations.AlterUniqueTogether(
            name='rating',
            unique_together=set([('user', 'resource')]),
        ),
    ]
