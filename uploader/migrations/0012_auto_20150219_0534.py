# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0011_auto_20150218_1807'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='author',
            field=models.CharField(default=0, max_length=200, verbose_name=b'Title'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='docfile',
            field=models.FileField(upload_to=b''),
            preserve_default=True,
        ),
    ]
