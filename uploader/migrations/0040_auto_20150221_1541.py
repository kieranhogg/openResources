# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0039_auto_20150221_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unittopic',
            name='topic',
            field=models.ManyToManyField(to='uploader.Topic', null=True, blank=True),
            preserve_default=True,
        ),
    ]
