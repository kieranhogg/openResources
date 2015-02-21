# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0016_auto_20150219_0649'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='licence',
            field=models.ForeignKey(to='uploader.Licence', null=True),
            preserve_default=True,
        ),
    ]
