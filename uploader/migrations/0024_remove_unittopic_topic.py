# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0023_auto_20150219_1615'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='unittopic',
            name='topic',
        ),
    ]
