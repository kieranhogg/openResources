# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0020_auto_20150219_0840'),
    ]

    operations = [
        migrations.AddField(
            model_name='examlevel',
            name='country',
            field=models.CharField(default=b'Any', max_length=200, verbose_name=b'Country'),
            preserve_default=True,
        ),
    ]
