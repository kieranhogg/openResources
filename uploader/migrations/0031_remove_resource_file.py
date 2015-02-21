# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0030_auto_20150220_1036'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resource',
            name='file',
        ),
    ]
