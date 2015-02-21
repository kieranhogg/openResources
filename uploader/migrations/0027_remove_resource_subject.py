# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0026_auto_20150220_0801'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resource',
            name='subject',
        ),
    ]
